from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.core.database import get_db
from app.utils.deps import get_current_trainer
from app.models import User, Client, Program
from app.models.program_assignment import ProgramAssignment as ProgramAssignmentModel
from app.schemas.program_assignment import (
    ProgramAssignmentCreate, ProgramAssignment as ProgramAssignmentSchema, 
    ProgramAssignmentUpdate, ProgramAssignmentWithDetails
)
from app.services.program_assignment_service import ProgramAssignmentService

router = APIRouter(tags=["program-assignments"])


@router.post("/", response_model=ProgramAssignmentSchema)
def create_program_assignment(
    assignment_data: ProgramAssignmentCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a new program assignment for a client"""
    try:
        assignment = ProgramAssignmentService.create_assignment(
            db, assignment_data, current_user.id
        )
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/", response_model=List[ProgramAssignmentWithDetails])
def get_trainer_assignments(
    client_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get all program assignments created by the trainer"""
    
    query = (
        db.query(ProgramAssignmentModel)
        .filter(ProgramAssignmentModel.trainer_id == current_user.id)
        .options(
            joinedload(ProgramAssignmentModel.client),
            joinedload(ProgramAssignmentModel.program)
        )
    )
    
    if client_id:
        query = query.filter(ProgramAssignmentModel.client_id == client_id)
    
    if status_filter:
        query = query.filter(ProgramAssignmentModel.status == status_filter)
    
    assignments = query.order_by(ProgramAssignmentModel.created_at.desc()).all()
    
    return [
        ProgramAssignmentWithDetails(
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
            client_email=assignment.client.email
        )
        for assignment in assignments
    ]


@router.get("/{assignment_id}", response_model=ProgramAssignmentWithDetails)
def get_assignment_details(
    assignment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get specific assignment details"""
    
    assignment = (
        db.query(ProgramAssignmentModel)
        .filter(
            ProgramAssignmentModel.id == assignment_id,
            ProgramAssignmentModel.trainer_id == current_user.id
        )
        .options(
            joinedload(ProgramAssignmentModel.client),
            joinedload(ProgramAssignmentModel.program)
        )
        .first()
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
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
        client_email=assignment.client.email
    )


@router.put("/{assignment_id}", response_model=ProgramAssignmentSchema)
def update_assignment(
    assignment_id: int,
    assignment_update: ProgramAssignmentUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update a program assignment"""
    try:
        assignment = ProgramAssignmentService.update_assignment(
            db, assignment_id, assignment_update, current_user.id
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Delete a program assignment"""
    
    success = ProgramAssignmentService.cancel_assignment(
        db, assignment_id, current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return {"message": "Assignment deleted successfully"}
