import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.models.program import Program
from app.models.program_assignment import ProgramAssignment
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus

logger = logging.getLogger(__name__)


class WeeklyExerciseService:
    @staticmethod
    async def generate_weekly_exercises_from_assignment(
        db: AsyncSession, program_assignment: ProgramAssignment
    ) -> List[WeeklyExerciseAssignment]:
        try:
            program = (
                await db.execute(
                    select(Program).where(Program.id == program_assignment.program_id)
                )
            ).scalar_one_or_none()
            if not program or not program.workout_structure:
                logger.warning(
                    f"No program or workout structure found for assignment {program_assignment.id}"
                )
                return []

            weekly_exercises: List[WeeklyExerciseAssignment] = []
            start_date = (
                program_assignment.start_date.date()
                if program_assignment.start_date
                else date.today()
            )

            program_weeks = program.duration_weeks or 4
            sessions_per_week = program.sessions_per_week or len(program.workout_structure)

            for week in range(1, program_weeks + 1):
                for day_data in program.workout_structure:
                    day_number = day_data.get("day", 1)

                    days_offset = ((week - 1) * 7) + (
                        (day_number - 1) * (7 // max(sessions_per_week, 1))
                    )
                    workout_date = start_date + timedelta(days=days_offset)

                    for exercise_index, exercise_data in enumerate(
                        day_data.get("exercises", [])
                    ):
                        weekly_exercise = WeeklyExerciseAssignment(
                            program_assignment_id=program_assignment.id,
                            client_id=program_assignment.client_id,
                            trainer_id=program_assignment.trainer_id,
                            exercise_id=exercise_data.get("exercise_id"),
                            assigned_date=date.today(),
                            due_date=workout_date,
                            week_number=week,
                            day_number=day_number,
                            exercise_order=exercise_index + 1,
                            sets=exercise_data.get("sets", 3),
                            reps=exercise_data.get("reps", "10"),
                            weight=exercise_data.get("weight", "bodyweight"),
                            rest_seconds=exercise_data.get("rest_seconds", 60),
                            exercise_notes=exercise_data.get("notes", ""),
                            status=WeeklyExerciseStatus.PENDING,
                        )
                        db.add(weekly_exercise)
                        weekly_exercises.append(weekly_exercise)

            await db.commit()
            logger.info(
                f"Generated {len(weekly_exercises)} weekly exercise assignments for "
                f"program assignment {program_assignment.id}"
            )
            return weekly_exercises
        except Exception as e:
            logger.error(f"Error generating weekly exercises: {e}")
            await db.rollback()
            return []

    @staticmethod
    async def get_client_weekly_exercises(
        db: AsyncSession,
        client_id: int,
        week_start: Optional[date] = None,
        status: Optional[WeeklyExerciseStatus] = None,
    ) -> List[WeeklyExerciseAssignment]:
        stmt = (
            select(WeeklyExerciseAssignment)
            .options(
                selectinload(WeeklyExerciseAssignment.exercise),
                selectinload(WeeklyExerciseAssignment.client),
                selectinload(WeeklyExerciseAssignment.trainer),
                selectinload(WeeklyExerciseAssignment.program_assignment).selectinload(
                    ProgramAssignment.program
                ),
            )
            .where(WeeklyExerciseAssignment.client_id == client_id)
        )
        if week_start:
            week_end = week_start + timedelta(days=6)
            stmt = stmt.where(
                WeeklyExerciseAssignment.due_date >= week_start,
                WeeklyExerciseAssignment.due_date <= week_end,
            )
        if status:
            stmt = stmt.where(WeeklyExerciseAssignment.status == status)
        stmt = stmt.order_by(
            WeeklyExerciseAssignment.due_date,
            WeeklyExerciseAssignment.day_number,
            WeeklyExerciseAssignment.exercise_order,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_current_week_exercises(
        db: AsyncSession, client_id: int
    ) -> List[WeeklyExerciseAssignment]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        return await WeeklyExerciseService.get_client_weekly_exercises(
            db=db, client_id=client_id, week_start=week_start
        )

    @staticmethod
    async def update_exercise_status(
        db: AsyncSession,
        exercise_assignment_id: int,
        status: WeeklyExerciseStatus,
        client_feedback: Optional[str] = None,
        completion_percentage: Optional[int] = None,
    ) -> Optional[WeeklyExerciseAssignment]:
        try:
            exercise = (
                await db.execute(
                    select(WeeklyExerciseAssignment).where(
                        WeeklyExerciseAssignment.id == exercise_assignment_id
                    )
                )
            ).scalar_one_or_none()
            if not exercise:
                return None

            exercise.status = status
            if client_feedback:
                exercise.client_feedback = client_feedback
            if completion_percentage is not None:
                exercise.completion_percentage = completion_percentage
            if status == WeeklyExerciseStatus.COMPLETED:
                exercise.completed_date = func.now()
                exercise.completion_percentage = 100

            await db.commit()
            return exercise
        except Exception as e:
            logger.error(f"Error updating exercise status: {e}")
            await db.rollback()
            return None

    @staticmethod
    async def delete_weekly_exercises_for_assignment(
        db: AsyncSession, program_assignment_id: int
    ) -> bool:
        try:
            stmt = sql_delete(WeeklyExerciseAssignment).where(
                WeeklyExerciseAssignment.program_assignment_id == program_assignment_id
            )
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting weekly exercises: {e}")
            await db.rollback()
            return False
