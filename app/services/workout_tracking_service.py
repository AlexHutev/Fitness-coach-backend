from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Client, ExerciseLog, ProgramAssignment, WorkoutLog
from app.schemas.client_schemas import (
    ExerciseLogResponse,
    WorkoutLogCreate,
    WorkoutLogResponse,
)


class WorkoutTrackingService:
    async def create_workout_log(
        self, db: AsyncSession, workout_data: WorkoutLogCreate, client_id: int
    ) -> Optional[WorkoutLogResponse]:
        assignment = (
            await db.execute(
                select(ProgramAssignment).where(
                    ProgramAssignment.id == workout_data.assignment_id,
                    ProgramAssignment.client_id == client_id,
                )
            )
        ).scalar_one_or_none()
        if not assignment:
            return None

        workout_log = WorkoutLog(
            assignment_id=workout_data.assignment_id,
            client_id=client_id,
            workout_date=workout_data.workout_date or datetime.now(),
            day_number=workout_data.day_number,
            workout_name=workout_data.workout_name,
            total_duration_minutes=workout_data.total_duration_minutes,
            perceived_exertion=workout_data.perceived_exertion,
            client_notes=workout_data.client_notes,
            is_completed=workout_data.is_completed,
            is_skipped=workout_data.is_skipped,
            skip_reason=workout_data.skip_reason,
        )
        db.add(workout_log)
        await db.flush()

        exercise_logs: List[ExerciseLog] = []
        for exercise_data in workout_data.exercises:
            exercise_log = ExerciseLog(
                workout_log_id=workout_log.id,
                exercise_id=exercise_data.exercise_id,
                exercise_name=exercise_data.exercise_name,
                exercise_order=exercise_data.exercise_order,
                planned_sets=exercise_data.planned_sets,
                planned_reps=exercise_data.planned_reps,
                planned_weight=exercise_data.planned_weight,
                planned_rest_seconds=exercise_data.planned_rest_seconds,
                actual_sets=[set_data.dict() for set_data in exercise_data.actual_sets],
                difficulty_rating=exercise_data.difficulty_rating,
                exercise_notes=exercise_data.exercise_notes,
                form_rating=exercise_data.form_rating,
            )
            db.add(exercise_log)
            exercise_logs.append(exercise_log)

        if workout_data.is_completed:
            assignment.completed_workouts += 1
            assignment.last_workout_date = workout_log.workout_date
            await self._notify_trainer_workout_completed(db, assignment, workout_log)

        await db.commit()
        await db.refresh(workout_log)
        return self._format_workout_response(workout_log, exercise_logs)

    async def get_workout_log(
        self, db: AsyncSession, workout_id: int, client_id: int
    ) -> Optional[WorkoutLogResponse]:
        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.id == workout_id, WorkoutLog.client_id == client_id)
        )
        workout_log = (await db.execute(stmt)).scalar_one_or_none()
        if not workout_log:
            return None
        return self._format_workout_response(workout_log, workout_log.exercise_logs)

    async def get_workout_logs_for_assignment(
        self,
        db: AsyncSession,
        assignment_id: int,
        client_id: int,
        limit: int = 50,
    ) -> List[WorkoutLogResponse]:
        assignment = (
            await db.execute(
                select(ProgramAssignment).where(
                    ProgramAssignment.id == assignment_id,
                    ProgramAssignment.client_id == client_id,
                )
            )
        ).scalar_one_or_none()
        if not assignment:
            return []

        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.assignment_id == assignment_id)
            .order_by(WorkoutLog.workout_date.desc())
            .limit(limit)
        )
        workout_logs = list((await db.execute(stmt)).scalars().all())
        return [self._format_workout_response(log, log.exercise_logs) for log in workout_logs]

    async def update_workout_log(
        self,
        db: AsyncSession,
        workout_id: int,
        client_id: int,
        update_data: dict,
    ) -> Optional[WorkoutLogResponse]:
        workout_log = (
            await db.execute(
                select(WorkoutLog).where(
                    WorkoutLog.id == workout_id,
                    WorkoutLog.client_id == client_id,
                )
            )
        ).scalar_one_or_none()
        if not workout_log:
            return None

        allowed_fields = {
            "total_duration_minutes",
            "perceived_exertion",
            "client_notes",
            "is_completed",
            "is_skipped",
            "skip_reason",
        }
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(workout_log, field):
                setattr(workout_log, field, value)

        await db.commit()
        await db.refresh(workout_log)

        # Reload with exercise logs eagerly
        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.id == workout_id)
        )
        workout_log = (await db.execute(stmt)).scalar_one()
        return self._format_workout_response(workout_log, workout_log.exercise_logs)

    async def update_exercise_log(
        self,
        db: AsyncSession,
        exercise_log_id: int,
        client_id: int,
        update_data: dict,
    ) -> Optional[ExerciseLogResponse]:
        stmt = (
            select(ExerciseLog)
            .join(WorkoutLog)
            .where(
                ExerciseLog.id == exercise_log_id,
                WorkoutLog.client_id == client_id,
            )
        )
        exercise_log = (await db.execute(stmt)).scalar_one_or_none()
        if not exercise_log:
            return None

        allowed_fields = {"actual_sets", "difficulty_rating", "exercise_notes", "form_rating"}
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(exercise_log, field):
                setattr(exercise_log, field, value)

        await db.commit()
        await db.refresh(exercise_log)

        return ExerciseLogResponse(
            id=exercise_log.id,
            exercise_name=exercise_log.exercise_name,
            exercise_id=exercise_log.exercise_id,
            exercise_order=exercise_log.exercise_order,
            planned_sets=exercise_log.planned_sets,
            planned_reps=exercise_log.planned_reps,
            planned_weight=exercise_log.planned_weight,
            planned_rest_seconds=exercise_log.planned_rest_seconds,
            actual_sets=exercise_log.actual_sets or [],
            difficulty_rating=exercise_log.difficulty_rating,
            exercise_notes=exercise_log.exercise_notes,
            form_rating=exercise_log.form_rating,
            created_at=exercise_log.created_at,
        )

    async def get_workout_history_summary(
        self, db: AsyncSession, assignment_id: int, client_id: int
    ) -> dict:
        assignment = (
            await db.execute(
                select(ProgramAssignment).where(
                    ProgramAssignment.id == assignment_id,
                    ProgramAssignment.client_id == client_id,
                )
            )
        ).scalar_one_or_none()
        if not assignment:
            return {}

        stats_stmt = (
            select(
                func.count(WorkoutLog.id).label("total_workouts"),
                func.count(func.nullif(WorkoutLog.is_completed, False)).label(
                    "completed_workouts"
                ),
                func.count(func.nullif(WorkoutLog.is_skipped, False)).label(
                    "skipped_workouts"
                ),
                func.avg(WorkoutLog.total_duration_minutes).label("avg_duration"),
                func.avg(WorkoutLog.perceived_exertion).label("avg_exertion"),
            )
            .where(WorkoutLog.assignment_id == assignment_id)
        )
        row = (await db.execute(stats_stmt)).first()
        if row is None:
            return {}

        total_workouts = row.total_workouts or 0
        completed_workouts = row.completed_workouts or 0
        return {
            "total_workouts": total_workouts,
            "completed_workouts": completed_workouts,
            "skipped_workouts": row.skipped_workouts or 0,
            "completion_rate": round(
                (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0,
                1,
            ),
            "average_duration": round(row.avg_duration, 1) if row.avg_duration else None,
            "average_exertion": round(row.avg_exertion, 1) if row.avg_exertion else None,
        }

    def _format_workout_response(
        self, workout_log: WorkoutLog, exercise_logs: List[ExerciseLog]
    ) -> WorkoutLogResponse:
        exercises = [
            ExerciseLogResponse(
                id=ex_log.id,
                exercise_name=ex_log.exercise_name,
                exercise_id=ex_log.exercise_id,
                exercise_order=ex_log.exercise_order,
                planned_sets=ex_log.planned_sets,
                planned_reps=ex_log.planned_reps,
                planned_weight=ex_log.planned_weight,
                planned_rest_seconds=ex_log.planned_rest_seconds,
                actual_sets=ex_log.actual_sets or [],
                difficulty_rating=ex_log.difficulty_rating,
                exercise_notes=ex_log.exercise_notes,
                form_rating=ex_log.form_rating,
                created_at=ex_log.created_at,
            )
            for ex_log in sorted(exercise_logs, key=lambda x: x.exercise_order)
        ]

        return WorkoutLogResponse(
            id=workout_log.id,
            assignment_id=workout_log.assignment_id,
            client_id=workout_log.client_id,
            workout_date=workout_log.workout_date,
            day_number=workout_log.day_number,
            workout_name=workout_log.workout_name,
            total_duration_minutes=workout_log.total_duration_minutes,
            perceived_exertion=workout_log.perceived_exertion,
            client_notes=workout_log.client_notes,
            trainer_feedback=workout_log.trainer_feedback,
            is_completed=workout_log.is_completed,
            is_skipped=workout_log.is_skipped,
            skip_reason=workout_log.skip_reason,
            exercises=exercises,
            created_at=workout_log.created_at,
        )

    async def _notify_trainer_workout_completed(
        self,
        db: AsyncSession,
        assignment: ProgramAssignment,
        workout_log: WorkoutLog,
    ) -> None:
        from app.services.notification_service import NotificationService

        client = (
            await db.execute(select(Client).where(Client.id == assignment.client_id))
        ).scalar_one_or_none()
        if not client:
            return

        await NotificationService.create_workout_completed_notification(
            db=db,
            trainer_id=client.trainer_id,
            client=client,
            workout_log=workout_log,
        )


workout_tracking_service = WorkoutTrackingService()
