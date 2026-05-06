from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.program import Program, ProgramCreate, ProgramList, ProgramUpdate
from app.schemas.program_assignment import (
    AssignmentRequest,
    BulkAssignmentCreate,
    ProgramAssignment,
)
from app.services.program_assignment_service import ProgramAssignmentService
from app.services.program_service import ProgramService
from app.utils.deps import get_current_trainer

router = APIRouter()


@router.post("/", response_model=Program, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    try:
        return await ProgramService.create_program(db, program_data, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating program: {e}",
        )


@router.get("/", response_model=List[ProgramList])
async def get_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    program_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    return await ProgramService.get_programs(
        db=db,
        trainer_id=current_user.id,
        skip=skip,
        limit=limit,
        program_type=program_type,
        difficulty_level=difficulty_level,
        is_template=is_template,
    )


@router.get("/search")
async def search_programs(
    search_term: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    return await ProgramService.search_programs(db, current_user.id, search_term)


@router.get("/{program_id}", response_model=Program)
async def get_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    program = await ProgramService.get_program(db, program_id, current_user.id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
        )
    return program


@router.put("/{program_id}", response_model=Program)
async def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    program = await ProgramService.update_program(
        db, program_id, program_update, current_user.id
    )
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
        )
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    success = await ProgramService.delete_program(db, program_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
        )


@router.post("/{program_id}/duplicate", response_model=Program)
async def duplicate_program(
    program_id: int,
    new_name: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    program = await ProgramService.duplicate_program(
        db, program_id, current_user.id, new_name
    )
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
        )
    return program


@router.post("/{program_id}/assign", response_model=List[ProgramAssignment])
async def assign_program(
    program_id: int,
    assignment_request: AssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    if not assignment_request.client_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one client must be selected",
        )

    bulk_data = BulkAssignmentCreate(
        program_id=program_id,
        client_ids=assignment_request.client_ids,
        start_date=assignment_request.start_date,
        custom_notes=assignment_request.custom_notes,
    )

    try:
        assignments = await ProgramAssignmentService.bulk_assign(
            db, bulk_data, current_user.id
        )
        if not assignments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No assignments were created. All selected clients may already have an active program assignment.",
            )
        return assignments
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/clients/{client_id}/active-assignment", response_model=Optional[ProgramAssignment]
)
async def get_client_active_assignment(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    return await ProgramAssignmentService.get_client_active_assignment(
        db, client_id, current_user.id
    )
