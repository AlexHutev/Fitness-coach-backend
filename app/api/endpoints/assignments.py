from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import User
from app.models.program_assignment import (
    AssignmentStatus,
    ProgramAssignment as ProgramAssignmentModel,
)
from app.schemas.program_assignment import (
    ProgramAssignment as ProgramAssignmentSchema,
    ProgramAssignmentCreate,
    ProgramAssignmentUpdate,
    ProgramAssignmentWithDetails,
)
from app.services.program_assignment_service import ProgramAssignmentService
from app.utils.deps import get_current_trainer

router = APIRouter(tags=["program-assignments"])


async def _enrich(db: AsyncSession, assignment: ProgramAssignmentModel) -> ProgramAssignmentWithDetails:
    enhanced_structure = await ProgramAssignmentService.enhance_workout_structure_with_exercise_names(
        db, assignment.program.workout_structure or []
    )
    return ProgramAssignmentWithDetails(
        id=assignment.id,
        program_id=assignment.program_id,
        client_id=assignment.client_id,
        trainer_id=assignment.trainer_id,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        custom_notes=assignment.custom_notes,
        trainer_notes=assignment.trainer_notes,
        assigned_date=assignment.assigned_date,
        status=assignment.status,
        completion_percentage=assignment.completion_percentage,
        sessions_completed=assignment.sessions_completed,
        total_sessions=assignment.total_sessions,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        client_name=f"{assignment.client.first_name} {assignment.client.last_name}",
        program_name=assignment.program.name,
        program_type=assignment.program.program_type.value,
        program_difficulty=assignment.program.difficulty_level.value,
        program_description=assignment.program.description,
        workout_structure=enhanced_structure,
        client_email=assignment.client.email,
    )


@router.post("/", response_model=ProgramAssignmentSchema)
async def create_program_assignment(
    assignment_data: ProgramAssignmentCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ProgramAssignmentService.create_assignment(
            db, assignment_data, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ProgramAssignmentWithDetails])
async def get_trainer_assignments(
    client_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ProgramAssignmentModel)
        .options(
            selectinload(ProgramAssignmentModel.client),
            selectinload(ProgramAssignmentModel.program),
        )
        .where(ProgramAssignmentModel.trainer_id == current_user.id)
    )

    if client_id:
        stmt = stmt.where(ProgramAssignmentModel.client_id == client_id)

    if status_filter:
        try:
            status_enum = AssignmentStatus(status_filter.lower())
            stmt = stmt.where(ProgramAssignmentModel.status == status_enum)
        except ValueError:
            stmt = stmt.where(ProgramAssignmentModel.status == "invalid_status")

    stmt = stmt.order_by(ProgramAssignmentModel.created_at.desc())
    assignments = list((await db.execute(stmt)).scalars().all())

    return [await _enrich(db, a) for a in assignments]


@router.get("/{assignment_id}", response_model=ProgramAssignmentWithDetails)
async def get_assignment_details(
    assignment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ProgramAssignmentModel)
        .options(
            selectinload(ProgramAssignmentModel.client),
            selectinload(ProgramAssignmentModel.program),
        )
        .where(
            ProgramAssignmentModel.id == assignment_id,
            ProgramAssignmentModel.trainer_id == current_user.id,
        )
    )
    assignment = (await db.execute(stmt)).scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    return await _enrich(db, assignment)


@router.put("/{assignment_id}", response_model=ProgramAssignmentSchema)
async def update_assignment(
    assignment_id: int,
    assignment_update: ProgramAssignmentUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    try:
        assignment = await ProgramAssignmentService.update_assignment(
            db, assignment_id, assignment_update, current_user.id
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    success = await ProgramAssignmentService.cancel_assignment(
        db, assignment_id, current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    return {"message": "Assignment deleted successfully"}
