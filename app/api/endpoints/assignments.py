from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.utils.deps import get_current_trainer
from app.models.user import User
from app.models.program import Program
from app.models.client import Client
from app.services.program_assignment_service import ProgramAssignmentService
from app.schemas.program_assignment import (
    ProgramAssignment, ProgramAssignmentUpdate, ProgramAssignmentWithDetails,
    ProgressUpdate, AssignmentRequest
)
from app.models.program_assignment import AssignmentStatus

router = APIRouter()


@router.get("/", response_model=List[ProgramAssignmentWithDetails])
def get_program_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get all program assignments for the current trainer"""
    
    # Convert string status to enum
    status_enum = None
    if status:
        try:
            status_enum = AssignmentStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    assignments = ProgramAssignmentService.get_assignments(
        db=db,
        trainer_id=current_user.id,
        skip=skip,
        limit=limit,
        client_id=client_id,
        status=status_enum
    )
    
    # Convert to detailed response with joined data
    detailed_assignments = []
    for assignment in assignments:
        # Load related data
        program = db.query(Program).filter(Program.id == assignment.program_id).first()
        client = db.query(Client).filter(Client.id == assignment.client_id).first()
        
        if program and client:
            detailed_assignment = {
                "id": assignment.id,
                "program_id": assignment.program_id,
                "client_id": assignment.client_id,
                "trainer_id": assignment.trainer_id,
                "assigned_date": assignment.assigned_date,
                "start_date": assignment.start_date,
                "end_date": assignment.end_date,
                "status": assignment.status,
                "custom_notes": assignment.custom_notes,
                "trainer_notes": assignment.trainer_notes,
                "completion_percentage": assignment.completion_percentage,
                "sessions_completed": assignment.sessions_completed,
                "total_sessions": assignment.total_sessions,
                "created_at": assignment.created_at,
                "updated_at": assignment.updated_at,
                "program_name": program.name,
                "program_type": program.program_type.value,
                "program_difficulty": program.difficulty_level.value,
                "client_name": f"{client.first_name} {client.last_name}",
                "client_email": client.email
            }
            detailed_assignments.append(detailed_assignment)
    
    return detailed_assignments


@router.get("/{assignment_id}", response_model=ProgramAssignment)
def get_program_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get a specific program assignment"""
    
    assignment = ProgramAssignmentService.get_assignment(db, assignment_id, current_user.id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return assignment


@router.put("/{assignment_id}", response_model=ProgramAssignment)
def update_program_assignment(
    assignment_id: int,
    assignment_update: ProgramAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Update a program assignment"""
    
    assignment = ProgramAssignmentService.update_assignment(
        db, assignment_id, assignment_update, current_user.id
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return assignment


@router.put("/{assignment_id}/progress", response_model=ProgramAssignment)
def update_assignment_progress(
    assignment_id: int,
    progress_update: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Update assignment progress"""
    
    assignment = ProgramAssignmentService.update_progress(
        db, assignment_id, progress_update, current_user.id
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_program_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Cancel a program assignment"""
    
    success = ProgramAssignmentService.cancel_assignment(db, assignment_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
