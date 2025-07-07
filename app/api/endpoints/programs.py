from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.utils.deps import get_current_trainer
from app.models.user import User
from app.models.program import Program
from app.models.client import Client
from app.services.program_service import ProgramService
from app.schemas.program import (
    ProgramCreate, ProgramUpdate, Program, ProgramList
)
from app.schemas.program_assignment import (
    ProgramAssignment, ProgramAssignmentUpdate, ProgramAssignmentWithDetails,
    ProgressUpdate, AssignmentRequest
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
    print(f"🎯 PUT /programs/{program_id} called by user {current_user.id}")
    print(f"📨 Request data type: {type(program_update)}")
    print(f"📨 Request data: {program_update}")
    
    try:
        # Add detailed logging
        print(f"🔧 Calling ProgramService.update_program...")
        program = ProgramService.update_program(db, program_id, program_update, current_user.id)
        if not program:
            print(f"❌ Program {program_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Program not found"
            )
        print(f"✅ Program updated successfully: {program.id}")
        return program
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"💥 Error updating program: {e}")
        print(f"📊 Traceback: {error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating program: {str(e)}"
        )


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



# Program Assignment endpoints
@router.post("/{program_id}/assign", response_model=List[ProgramAssignment])
def assign_program(
    program_id: int,
    assignment_request: AssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Assign a program to one or more clients"""
    from app.services.program_assignment_service import ProgramAssignmentService
    from app.schemas.program_assignment import BulkAssignmentCreate, AssignmentRequest
    
    # Validate that we have client IDs
    if not assignment_request.client_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one client must be selected"
        )
    
    # Create bulk assignment data with program_id from URL
    bulk_data = BulkAssignmentCreate(
        program_id=program_id,
        client_ids=assignment_request.client_ids,
        start_date=assignment_request.start_date,
        custom_notes=assignment_request.custom_notes
    )
    
    try:
        assignments = ProgramAssignmentService.bulk_assign(db, bulk_data, current_user.id)
        
        # If no assignments were created, provide helpful feedback
        if not assignments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No assignments were created. All selected clients may already have active program assignments."
            )
        
        return assignments
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


@router.get("/clients/{client_id}/active-assignment", response_model=Optional[ProgramAssignment])
def get_client_active_assignment(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get client's active program assignment"""
    from app.services.program_assignment_service import ProgramAssignmentService
    
    assignment = ProgramAssignmentService.get_client_active_assignment(
        db, client_id, current_user.id
    )
    return assignment
