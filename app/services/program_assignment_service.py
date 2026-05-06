import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.program import Exercise, Program
from app.models.program_assignment import AssignmentStatus, ProgramAssignment
from app.schemas.program_assignment import (
    BulkAssignmentCreate,
    ProgramAssignmentCreate,
    ProgramAssignmentUpdate,
    ProgressUpdate,
)

logger = logging.getLogger(__name__)


class ProgramAssignmentService:
    @staticmethod
    async def create_assignment(
        db: AsyncSession,
        assignment_data: ProgramAssignmentCreate,
        trainer_id: int,
    ) -> ProgramAssignment:
        program = (
            await db.execute(
                select(Program).where(
                    and_(
                        Program.id == assignment_data.program_id,
                        Program.trainer_id == trainer_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not program:
            raise ValueError("Program not found or access denied")

        client = (
            await db.execute(
                select(Client).where(
                    and_(
                        Client.id == assignment_data.client_id,
                        Client.trainer_id == trainer_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not client:
            raise ValueError("Client not found or access denied")

        existing = (
            await db.execute(
                select(ProgramAssignment).where(
                    and_(
                        ProgramAssignment.client_id == assignment_data.client_id,
                        ProgramAssignment.status == AssignmentStatus.ACTIVE,
                    )
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Client already has an active program assignment")

        total_sessions = None
        if program.duration_weeks and program.sessions_per_week:
            total_sessions = program.duration_weeks * program.sessions_per_week

        assignment = ProgramAssignment(
            program_id=assignment_data.program_id,
            client_id=assignment_data.client_id,
            trainer_id=trainer_id,
            start_date=assignment_data.start_date,
            end_date=assignment_data.end_date,
            custom_notes=assignment_data.custom_notes,
            trainer_notes=assignment_data.trainer_notes,
            total_sessions=total_sessions,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        try:
            from app.services.weekly_exercise_service import WeeklyExerciseService

            await WeeklyExerciseService.generate_weekly_exercises_from_assignment(
                db, assignment
            )
        except Exception as e:
            logger.warning(
                f"Failed to generate weekly exercises for assignment {assignment.id}: {e}"
            )

        return assignment

    @staticmethod
    async def get_assignments(
        db: AsyncSession,
        trainer_id: int,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[int] = None,
        status: Optional[AssignmentStatus] = None,
    ) -> List[ProgramAssignment]:
        stmt = select(ProgramAssignment).where(
            ProgramAssignment.trainer_id == trainer_id
        )
        if client_id:
            stmt = stmt.where(ProgramAssignment.client_id == client_id)
        if status:
            stmt = stmt.where(ProgramAssignment.status == status)

        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_assignment(
        db: AsyncSession, assignment_id: int, trainer_id: int
    ) -> Optional[ProgramAssignment]:
        stmt = select(ProgramAssignment).where(
            and_(
                ProgramAssignment.id == assignment_id,
                ProgramAssignment.trainer_id == trainer_id,
            )
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def update_assignment(
        db: AsyncSession,
        assignment_id: int,
        assignment_update: ProgramAssignmentUpdate,
        trainer_id: int,
    ) -> Optional[ProgramAssignment]:
        assignment = await ProgramAssignmentService.get_assignment(
            db, assignment_id, trainer_id
        )
        if not assignment:
            return None
        for field, value in assignment_update.dict(exclude_unset=True).items():
            setattr(assignment, field, value)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def update_progress(
        db: AsyncSession,
        assignment_id: int,
        progress_update: ProgressUpdate,
        trainer_id: int,
    ) -> Optional[ProgramAssignment]:
        assignment = await ProgramAssignmentService.get_assignment(
            db, assignment_id, trainer_id
        )
        if not assignment:
            return None
        assignment.sessions_completed = progress_update.sessions_completed
        assignment.completion_percentage = progress_update.completion_percentage
        if progress_update.notes:
            assignment.trainer_notes = progress_update.notes
        if progress_update.completion_percentage >= 100:
            assignment.status = AssignmentStatus.COMPLETED
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def cancel_assignment(
        db: AsyncSession, assignment_id: int, trainer_id: int
    ) -> bool:
        assignment = await ProgramAssignmentService.get_assignment(
            db, assignment_id, trainer_id
        )
        if not assignment:
            return False
        assignment.status = AssignmentStatus.CANCELLED
        await db.commit()
        return True

    @staticmethod
    async def bulk_assign(
        db: AsyncSession,
        bulk_data: BulkAssignmentCreate,
        trainer_id: int,
    ) -> List[ProgramAssignment]:
        program = (
            await db.execute(
                select(Program).where(
                    and_(Program.id == bulk_data.program_id, Program.trainer_id == trainer_id)
                )
            )
        ).scalar_one_or_none()
        if not program:
            raise ValueError("Program not found or access denied")

        assignments: List[ProgramAssignment] = []
        errors: List[str] = []

        for client_id in bulk_data.client_ids:
            try:
                client = (
                    await db.execute(
                        select(Client).where(
                            and_(Client.id == client_id, Client.trainer_id == trainer_id)
                        )
                    )
                ).scalar_one_or_none()
                if not client:
                    errors.append(f"Client {client_id} not found or access denied")
                    continue

                existing = (
                    await db.execute(
                        select(ProgramAssignment).where(
                            and_(
                                ProgramAssignment.client_id == client_id,
                                ProgramAssignment.status == AssignmentStatus.ACTIVE,
                            )
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    errors.append(
                        f"Client {client.first_name} {client.last_name} already has an active program assignment"
                    )
                    continue

                total_sessions = None
                if program.duration_weeks and program.sessions_per_week:
                    total_sessions = program.duration_weeks * program.sessions_per_week

                assignment = ProgramAssignment(
                    program_id=bulk_data.program_id,
                    client_id=client_id,
                    trainer_id=trainer_id,
                    start_date=bulk_data.start_date,
                    custom_notes=bulk_data.custom_notes,
                    total_sessions=total_sessions,
                )
                db.add(assignment)
                await db.flush()

                try:
                    from app.services.weekly_exercise_service import WeeklyExerciseService

                    await WeeklyExerciseService.generate_weekly_exercises_from_assignment(
                        db, assignment
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to generate weekly exercises for assignment {assignment.id}: {e}"
                    )

                assignments.append(assignment)
            except Exception as e:
                errors.append(f"Error assigning to client {client_id}: {e}")
                continue

        if assignments:
            try:
                await db.commit()
                for assignment in assignments:
                    await db.refresh(assignment)
            except Exception as e:
                await db.rollback()
                raise ValueError(f"Failed to save assignments: {e}")

        if not assignments and errors:
            raise ValueError(f"No assignments created. Errors: {'; '.join(errors)}")

        return assignments

    @staticmethod
    async def get_client_active_assignment(
        db: AsyncSession, client_id: int, trainer_id: int
    ) -> Optional[ProgramAssignment]:
        stmt = select(ProgramAssignment).where(
            and_(
                ProgramAssignment.client_id == client_id,
                ProgramAssignment.trainer_id == trainer_id,
                ProgramAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def enhance_workout_structure_with_exercise_names(
        db: AsyncSession, workout_structure: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not workout_structure:
            return workout_structure

        exercise_ids: set[int] = set()
        for day in workout_structure:
            for exercise in day.get("exercises", []):
                if "exercise_id" in exercise:
                    exercise_ids.add(exercise["exercise_id"])

        if exercise_ids:
            stmt = select(Exercise.id, Exercise.name).where(Exercise.id.in_(exercise_ids))
            rows = (await db.execute(stmt)).all()
            exercise_name_map = {row.id: row.name for row in rows}
        else:
            exercise_name_map = {}

        enhanced_structure: List[Dict[str, Any]] = []
        for day in workout_structure:
            enhanced_day = day.copy()
            if "exercises" in enhanced_day:
                enhanced_exercises = []
                for exercise in enhanced_day["exercises"]:
                    enhanced_exercise = exercise.copy()
                    if "exercise_id" in enhanced_exercise:
                        eid = enhanced_exercise["exercise_id"]
                        enhanced_exercise["exercise_name"] = exercise_name_map.get(
                            eid, f"Exercise {eid}"
                        )
                    enhanced_exercises.append(enhanced_exercise)
                enhanced_day["exercises"] = enhanced_exercises
            enhanced_structure.append(enhanced_day)
        return enhanced_structure
