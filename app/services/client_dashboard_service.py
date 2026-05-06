from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Client,
    Exercise,
    ExerciseLog,  # noqa: F401
    Program,
    ProgramAssignment,
    WorkoutLog,
)
from app.schemas.client_schemas import (
    ClientDashboardProgram,
    ClientDashboardResponse,
    ClientProgressStats,
    ExerciseLogResponse,
    ProgramTemplateForClient,
    WorkoutDayTemplate,
    WorkoutExerciseTemplate,
    WorkoutLogResponse,
)


class ClientDashboardService:
    async def get_client_dashboard(
        self, db: AsyncSession, client_id: int
    ) -> Optional[ClientDashboardResponse]:
        client = (
            await db.execute(select(Client).where(Client.id == client_id))
        ).scalar_one_or_none()
        if not client:
            return None

        active_programs = await self._get_active_programs(db, client_id)
        recent_workouts = await self._get_recent_workouts(db, client_id, limit=10)
        progress_stats = await self._get_progress_stats(db, client_id)

        return ClientDashboardResponse(
            client_id=client_id,
            client_name=f"{client.first_name} {client.last_name}",
            active_programs=active_programs,
            recent_workouts=recent_workouts,
            progress_stats=progress_stats,
        )

    async def _get_active_programs(
        self, db: AsyncSession, client_id: int
    ) -> List[ClientDashboardProgram]:
        stmt = (
            select(ProgramAssignment)
            .options(selectinload(ProgramAssignment.program))
            .join(Program)
            .where(ProgramAssignment.client_id == client_id)
            .where(ProgramAssignment.status == "active")
        )
        assignments = list((await db.execute(stmt)).scalars().all())

        programs: List[ClientDashboardProgram] = []
        for assignment in assignments:
            program = assignment.program

            completion_percentage = 0.0
            if assignment.total_workouts > 0:
                completion_percentage = (
                    assignment.completed_workouts / assignment.total_workouts
                ) * 100

            next_workout_day = await self._get_next_workout_day(db, assignment.id)

            programs.append(
                ClientDashboardProgram(
                    assignment_id=assignment.id,
                    program_id=program.id,
                    program_name=program.name,
                    program_description=program.description,
                    program_type=program.program_type.value,
                    difficulty_level=program.difficulty_level.value,
                    start_date=assignment.start_date,
                    end_date=assignment.end_date,
                    status=assignment.status,
                    total_workouts=assignment.total_workouts,
                    completed_workouts=assignment.completed_workouts,
                    completion_percentage=round(completion_percentage, 1),
                    last_workout_date=assignment.last_workout_date,
                    next_workout_day=next_workout_day,
                )
            )
        return programs

    async def _get_recent_workouts(
        self, db: AsyncSession, client_id: int, limit: int = 10
    ) -> List[WorkoutLogResponse]:
        stmt = (
            select(WorkoutLog)
            .options(selectinload(WorkoutLog.exercise_logs))
            .where(WorkoutLog.client_id == client_id)
            .order_by(desc(WorkoutLog.workout_date))
            .limit(limit)
        )
        workout_logs = list((await db.execute(stmt)).scalars().all())

        workouts: List[WorkoutLogResponse] = []
        for log in workout_logs:
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
                for ex_log in sorted(log.exercise_logs, key=lambda x: x.exercise_order)
            ]
            workouts.append(
                WorkoutLogResponse(
                    id=log.id,
                    assignment_id=log.assignment_id,
                    client_id=log.client_id,
                    workout_date=log.workout_date,
                    day_number=log.day_number,
                    workout_name=log.workout_name,
                    total_duration_minutes=log.total_duration_minutes,
                    perceived_exertion=log.perceived_exertion,
                    client_notes=log.client_notes,
                    trainer_feedback=log.trainer_feedback,
                    is_completed=log.is_completed,
                    is_skipped=log.is_skipped,
                    skip_reason=log.skip_reason,
                    exercises=exercises,
                    created_at=log.created_at,
                )
            )
        return workouts

    async def _get_progress_stats(
        self, db: AsyncSession, client_id: int
    ) -> ClientProgressStats:
        async def _scalar_count(stmt) -> int:
            return int((await db.execute(stmt)).scalar_one())

        total_programs = await _scalar_count(
            select(func.count())
            .select_from(ProgramAssignment)
            .where(ProgramAssignment.client_id == client_id)
        )
        active_programs = await _scalar_count(
            select(func.count())
            .select_from(ProgramAssignment)
            .where(
                ProgramAssignment.client_id == client_id,
                ProgramAssignment.status == "active",
            )
        )
        completed_programs = await _scalar_count(
            select(func.count())
            .select_from(ProgramAssignment)
            .where(
                ProgramAssignment.client_id == client_id,
                ProgramAssignment.status == "completed",
            )
        )
        total_workouts_completed = await _scalar_count(
            select(func.count())
            .select_from(WorkoutLog)
            .where(
                WorkoutLog.client_id == client_id,
                WorkoutLog.is_completed.is_(True),
            )
        )

        current_streak = await self._calculate_current_streak(db, client_id)
        longest_streak = await self._calculate_longest_streak(db, client_id)

        avg_duration = (
            await db.execute(
                select(func.avg(WorkoutLog.total_duration_minutes)).where(
                    WorkoutLog.client_id == client_id,
                    WorkoutLog.is_completed.is_(True),
                    WorkoutLog.total_duration_minutes.isnot(None),
                )
            )
        ).scalar()
        avg_exertion = (
            await db.execute(
                select(func.avg(WorkoutLog.perceived_exertion)).where(
                    WorkoutLog.client_id == client_id,
                    WorkoutLog.is_completed.is_(True),
                    WorkoutLog.perceived_exertion.isnot(None),
                )
            )
        ).scalar()

        return ClientProgressStats(
            total_programs=total_programs,
            active_programs=active_programs,
            completed_programs=completed_programs,
            total_workouts_completed=total_workouts_completed,
            current_streak=current_streak,
            longest_streak=longest_streak,
            average_workout_duration=round(avg_duration, 1) if avg_duration else None,
            average_perceived_exertion=round(avg_exertion, 1) if avg_exertion else None,
        )

    async def _get_next_workout_day(
        self, db: AsyncSession, assignment_id: int
    ) -> Optional[int]:
        latest_workout = (
            await db.execute(
                select(WorkoutLog)
                .where(WorkoutLog.assignment_id == assignment_id)
                .order_by(desc(WorkoutLog.day_number))
                .limit(1)
            )
        ).scalar_one_or_none()
        if not latest_workout:
            return 1

        assignment = (
            await db.execute(
                select(ProgramAssignment)
                .options(selectinload(ProgramAssignment.program))
                .where(ProgramAssignment.id == assignment_id)
            )
        ).scalar_one_or_none()
        if not assignment or not assignment.program.workout_structure:
            return None

        total_days = len(assignment.program.workout_structure)
        if latest_workout.day_number >= total_days:
            return 1
        return latest_workout.day_number + 1

    async def _calculate_current_streak(self, db: AsyncSession, client_id: int) -> int:
        result = await db.execute(
            select(WorkoutLog.workout_date)
            .where(
                WorkoutLog.client_id == client_id,
                WorkoutLog.is_completed.is_(True),
            )
            .order_by(desc(WorkoutLog.workout_date))
        )
        workouts = list(result.all())
        if not workouts:
            return 0

        streak = 0
        current_date = datetime.now().date()
        for (workout_date,) in workouts:
            d = workout_date.date()
            days_diff = (current_date - d).days
            if days_diff <= 2:
                streak += 1
                current_date = d
            else:
                break
        return streak

    async def _calculate_longest_streak(self, db: AsyncSession, client_id: int) -> int:
        result = await db.execute(
            select(WorkoutLog.workout_date)
            .where(
                WorkoutLog.client_id == client_id,
                WorkoutLog.is_completed.is_(True),
            )
            .order_by(WorkoutLog.workout_date)
        )
        workouts = [row[0] for row in result.all()]
        if not workouts:
            return 0

        max_streak = 0
        current_streak = 1
        prev_date = workouts[0].date()
        for i in range(1, len(workouts)):
            d = workouts[i].date()
            days_diff = (d - prev_date).days
            if days_diff <= 2:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
            prev_date = d
        return max(max_streak, current_streak)

    async def get_program_template_for_client(
        self, db: AsyncSession, assignment_id: int
    ) -> Optional[ProgramTemplateForClient]:
        assignment = (
            await db.execute(
                select(ProgramAssignment)
                .options(selectinload(ProgramAssignment.program))
                .where(ProgramAssignment.id == assignment_id)
            )
        ).scalar_one_or_none()
        if not assignment or not assignment.program:
            return None

        program = assignment.program

        workout_days: List[WorkoutDayTemplate] = []
        if program.workout_structure:
            for day_data in program.workout_structure:
                exercises: List[WorkoutExerciseTemplate] = []
                for ex_data in day_data.get("exercises", []):
                    exercise_details = None
                    if ex_data.get("exercise_id"):
                        exercise_details = (
                            await db.execute(
                                select(Exercise).where(Exercise.id == ex_data["exercise_id"])
                            )
                        ).scalar_one_or_none()

                    exercises.append(
                        WorkoutExerciseTemplate(
                            exercise_id=ex_data.get("exercise_id"),
                            exercise_name=ex_data.get("name", "Unknown Exercise"),
                            sets=ex_data.get("sets", 1),
                            reps=ex_data.get("reps", "1"),
                            weight=ex_data.get("weight"),
                            rest_seconds=ex_data.get("rest_seconds", 60),
                            notes=ex_data.get("notes"),
                            muscle_groups=exercise_details.muscle_groups
                            if exercise_details
                            else [],
                            equipment=exercise_details.equipment if exercise_details else [],
                            instructions=exercise_details.instructions
                            if exercise_details
                            else None,
                        )
                    )

                workout_days.append(
                    WorkoutDayTemplate(
                        day=day_data.get("day", 1),
                        name=day_data.get("name", f"Day {day_data.get('day', 1)}"),
                        exercises=exercises,
                    )
                )

        return ProgramTemplateForClient(
            program_id=program.id,
            assignment_id=assignment.id,
            program_name=program.name,
            program_description=program.description,
            program_type=program.program_type.value,
            difficulty_level=program.difficulty_level.value,
            duration_weeks=program.duration_weeks,
            sessions_per_week=program.sessions_per_week,
            workout_structure=workout_days,
            trainer_notes=assignment.assignment_notes,
        )


client_dashboard_service = ClientDashboardService()
