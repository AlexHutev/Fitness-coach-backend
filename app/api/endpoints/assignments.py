from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.database import get_db
from app.utils.deps import get_current_user
from app.services.client_auth_service import client_auth_service
from app.services.workout_tracking_service import workout_tracking_service
from app.models import User, ProgramAssignment, Client, Program
from app.schemas.client_schemas import (
    ProgramAssignmentCreate, ProgramAssignmentResponse, 
    ProgramAssignmentUpdate, ClientCreateCredentials
)


router = APIRouter(prefix="/api/v1/assignments", tags=["program-assignments"])


@router.post("/", response_model=ProgramAssignmentResponse)
def create_program_assignment(
    assignment_data: ProgramAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new program assignment for a client"""
    
    # Verify client belongs to trainer
    client = db.query(Client).filter(
        Client.id == assignment_data.client_id,
        Client.trainer_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or not assigned to you"
        )
    
    # Verify program belongs to trainer
    program = db.query(Program).filter(
        Program.id == assignment_data.program_id,
        Program.trainer_id == current_user.id
    ).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found or not created by you"
        )
    
    # Calculate total workouts based on program structure
    total_workouts = 0
    if program.workout_structure and assignment_data.end_date:
        weeks = (assignment_data.end_date - assignment_data.start_date).days // 7
        days_per_week = len(program.workout_structure)
        total_workouts = weeks * days_per_week
    
    # Create assignment
    assignment = ProgramAssignment(
        trainer_id=current_user.id,
        client_id=assignment_data.client_id,
        program_id=assignment_data.program_id,
        start_date=assignment_data.start_date,
        end_date=assignment_data.end_date,
        assignment_notes=assignment_data.assignment_notes,
        total_workouts=total_workouts
    )
    
    db.add(assignment)
    db.flush()  # Get ID without committing
    
    # Set up client credentials if provided
    if assignment_data.client_access_email and assignment_data.client_password:
        success = client_auth_service.create_client_credentials(
            db, assignment.id, assignment_data.client_access_email, assignment_data.client_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use for client access"
            )
    
    db.commit()
    db.refresh(assignment)
    
    return ProgramAssignmentResponse(
        id=assignment.id,
        trainer_id=assignment.trainer_id,
        client_id=assignment.client_id,
        program_id=assignment.program_id,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        status=assignment.status,
        total_workouts=assignment.total_workouts,
        completed_workouts=assignment.completed_workouts,
        last_workout_date=assignment.last_workout_date,
        assignment_notes=assignment.assignment_notes,
        trainer_feedback=assignment.trainer_feedback,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        client_name=f"{client.first_name} {client.last_name}",
        program_name=program.name
    )


@router.get("/", response_model=List[ProgramAssignmentResponse])
def get_trainer_assignments(
    client_id: int = None,
    status_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all program assignments created by the trainer"""
    
    query = (
        db.query(ProgramAssignment)
        .filter(ProgramAssignment.trainer_id == current_user.id)
        .options(
            joinedload(ProgramAssignment.client),
            joinedload(ProgramAssignment.program)
        )
    )
    
    if client_id:
        query = query.filter(ProgramAssignment.client_id == client_id)
    
    if status_filter:
        query = query.filter(ProgramAssignment.status == status_filter)
    
    assignments = query.order_by(ProgramAssignment.created_at.desc()).all()
    
    return [
        ProgramAssignmentResponse(
            id=assignment.id,
            trainer_id=assignment.trainer_id,
            client_id=assignment.client_id,
            program_id=assignment.program_id,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            status=assignment.status,
            total_workouts=assignment.total_workouts,
            completed_workouts=assignment.completed_workouts,
            last_workout_date=assignment.last_workout_date,
            assignment_notes=assignment.assignment_notes,
            trainer_feedback=assignment.trainer_feedback,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            client_name=f"{assignment.client.first_name} {assignment.client.last_name}",
            program_name=assignment.program.name
        )
        for assignment in assignments
    ]


@router.get("/{assignment_id}", response_model=ProgramAssignmentResponse)
def get_assignment_details(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific assignment details"""
    
    assignment = (
        db.query(ProgramAssignment)
        .filter(
            ProgramAssignment.id == assignment_id,
            ProgramAssignment.trainer_id == current_user.id
        )
        .options(
            joinedload(ProgramAssignment.client),
            joinedload(ProgramAssignment.program)
        )
        .first()
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return ProgramAssignmentResponse(
        id=assignment.id,
        trainer_id=assignment.trainer_id,
        client_id=assignment.client_id,
        program_id=assignment.program_id,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        status=assignment.status,
        total_workouts=assignment.total_workouts,
        completed_workouts=assignment.completed_workouts,
        last_workout_date=assignment.last_workout_date,
        assignment_notes=assignment.assignment_notes,
        trainer_feedback=assignment.trainer_feedback,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        client_name=f"{assignment.client.first_name} {assignment.client.last_name}",
        program_name=assignment.program.name
    )


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a program assignment"""
    
    assignment = (
        db.query(ProgramAssignment)
        .filter(
            ProgramAssignment.id == assignment_id,
            ProgramAssignment.trainer_id == current_user.id
        )
        .first()
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Assignment deleted successfully"}