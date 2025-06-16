from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.deps import get_current_trainer
from app.models.user import User
from app.services.program_service import ProgramService
from app.schemas.program import (
    ProgramCreate, ProgramUpdate, Program, ProgramList, ProgramAssignment
)

router = APIRouter()


@router.post("/", response_model=Program, status_code=status.HTTP_201_CREATED)
def create_program(
    program_data: ProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Create a new training program"""
    try:
        program = ProgramService.create_program(db, program_data, current_user.id)
        return program
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating program: {str(e)}"
        )


@router.get("/", response_model=List[ProgramList])
def get_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    program_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get all programs for the current trainer"""
    programs = ProgramService.get_programs(
        db=db,
        trainer_id=current_user.id,
        skip=skip,
        limit=limit,
        program_type=program_type,
        difficulty_level=difficulty_level,
        is_template=is_template
    )
    return programs


@router.get("/search")
def search_programs(
    search_term: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Search programs by name, description, or tags"""
    programs = ProgramService.search_programs(db, current_user.id, search_term)
    return programs


@router.get("/{program_id}", response_model=Program)
def get_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get a specific program by ID"""
    program = ProgramService.get_program(db, program_id, current_user.id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return program


@router.put("/{program_id}", response_model=Program)
def update_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Update an existing program"""
    program = ProgramService.update_program(db, program_id, program_update, current_user.id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Delete a program"""
    success = ProgramService.delete_program(db, program_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )


@router.post("/{program_id}/duplicate", response_model=Program)
def duplicate_program(
    program_id: int,
    new_name: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Create a copy of an existing program"""
    program = ProgramService.duplicate_program(db, program_id, current_user.id, new_name)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found"
        )
    return program
