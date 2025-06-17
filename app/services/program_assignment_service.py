from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from app.models.program_assignment import ProgramAssignment, AssignmentStatus
from app.models.program import Program
from app.models.client import Client
from app.schemas.program_assignment import (
    ProgramAssignmentCreate, 
    ProgramAssignmentUpdate,
    BulkAssignmentCreate,
    ProgressUpdate
)


class ProgramAssignmentService:
    
    @staticmethod
    def create_assignment(
        db: Session,
        assignment_data: ProgramAssignmentCreate,
        trainer_id: int
    ) -> ProgramAssignment:
        """Create a new program assignment"""
        
        # Verify program belongs to trainer
        program = db.query(Program).filter(
            and_(Program.id == assignment_data.program_id, Program.trainer_id == trainer_id)
        ).first()
        if not program:
            raise ValueError("Program not found or access denied")
        
        # Verify client belongs to trainer  
        client = db.query(Client).filter(
            and_(Client.id == assignment_data.client_id, Client.trainer_id == trainer_id)
        ).first()
        if not client:
            raise ValueError("Client not found or access denied")
        
        # Check for existing active assignment
        existing = db.query(ProgramAssignment).filter(
            and_(
                ProgramAssignment.client_id == assignment_data.client_id,
                ProgramAssignment.status == AssignmentStatus.ACTIVE
            )
        ).first()
        if existing:
            raise ValueError("Client already has an active program assignment")
        
        # Calculate total sessions if program has duration
        total_sessions = None
        if program.duration_weeks and program.sessions_per_week:
            total_sessions = program.duration_weeks * program.sessions_per_week        
        # Create the assignment
        assignment = ProgramAssignment(
            program_id=assignment_data.program_id,
            client_id=assignment_data.client_id,
            trainer_id=trainer_id,
            start_date=assignment_data.start_date,
            end_date=assignment_data.end_date,
            custom_notes=assignment_data.custom_notes,
            trainer_notes=assignment_data.trainer_notes,
            total_sessions=total_sessions
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def get_assignments(
        db: Session,
        trainer_id: int,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[int] = None,
        status: Optional[AssignmentStatus] = None
    ) -> List[ProgramAssignment]:
        """Get assignments for a trainer with optional filters"""
        
        query = db.query(ProgramAssignment).filter(
            ProgramAssignment.trainer_id == trainer_id
        )
        
        if client_id:
            query = query.filter(ProgramAssignment.client_id == client_id)
        
        if status:
            query = query.filter(ProgramAssignment.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_assignment(
        db: Session,
        assignment_id: int,
        trainer_id: int
    ) -> Optional[ProgramAssignment]:
        """Get a specific assignment by ID"""        
        return db.query(ProgramAssignment).filter(
            and_(
                ProgramAssignment.id == assignment_id,
                ProgramAssignment.trainer_id == trainer_id
            )
        ).first()
    
    @staticmethod
    def update_assignment(
        db: Session,
        assignment_id: int,
        assignment_update: ProgramAssignmentUpdate,
        trainer_id: int
    ) -> Optional[ProgramAssignment]:
        """Update an existing assignment"""
        
        assignment = ProgramAssignmentService.get_assignment(db, assignment_id, trainer_id)
        if not assignment:
            return None
        
        # Update fields
        update_data = assignment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def update_progress(
        db: Session,
        assignment_id: int,
        progress_update: ProgressUpdate,
        trainer_id: int
    ) -> Optional[ProgramAssignment]:
        """Update assignment progress"""
        
        assignment = ProgramAssignmentService.get_assignment(db, assignment_id, trainer_id)
        if not assignment:
            return None        
        assignment.sessions_completed = progress_update.sessions_completed
        assignment.completion_percentage = progress_update.completion_percentage
        
        if progress_update.notes:
            assignment.trainer_notes = progress_update.notes
        
        # Auto-complete if 100%
        if progress_update.completion_percentage >= 100:
            assignment.status = AssignmentStatus.COMPLETED
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def cancel_assignment(
        db: Session,
        assignment_id: int,
        trainer_id: int
    ) -> bool:
        """Cancel an assignment"""
        
        assignment = ProgramAssignmentService.get_assignment(db, assignment_id, trainer_id)
        if not assignment:
            return False
        
        assignment.status = AssignmentStatus.CANCELLED
        db.commit()
        return True
    
    @staticmethod
    def bulk_assign(
        db: Session,
        bulk_data: BulkAssignmentCreate,
        trainer_id: int
    ) -> List[ProgramAssignment]:
        """Assign a program to multiple clients"""
        
        # Verify program belongs to trainer
        program = db.query(Program).filter(
            and_(Program.id == bulk_data.program_id, Program.trainer_id == trainer_id)
        ).first()
        if not program:
            raise ValueError("Program not found or access denied")
        
        assignments = []
        errors = []
        
        for client_id in bulk_data.client_ids:
            try:
                # Verify client belongs to trainer
                client = db.query(Client).filter(
                    and_(Client.id == client_id, Client.trainer_id == trainer_id)
                ).first()
                if not client:
                    errors.append(f"Client {client_id} not found or access denied")
                    continue
                
                # Check for existing active assignment
                existing = db.query(ProgramAssignment).filter(
                    and_(
                        ProgramAssignment.client_id == client_id,
                        ProgramAssignment.status == AssignmentStatus.ACTIVE
                    )
                ).first()
                if existing:
                    errors.append(f"Client {client.first_name} {client.last_name} already has an active program assignment")
                    continue
                
                # Calculate total sessions
                total_sessions = None
                if program.duration_weeks and program.sessions_per_week:
                    total_sessions = program.duration_weeks * program.sessions_per_week
                
                assignment = ProgramAssignment(
                    program_id=bulk_data.program_id,
                    client_id=client_id,
                    trainer_id=trainer_id,
                    start_date=bulk_data.start_date,
                    custom_notes=bulk_data.custom_notes,
                    total_sessions=total_sessions
                )
                
                db.add(assignment)
                assignments.append(assignment)
                
            except Exception as e:
                errors.append(f"Error assigning to client {client_id}: {str(e)}")
                continue
        
        if assignments:
            try:
                db.commit()
                # Refresh all assignments to get the generated IDs and computed fields
                for assignment in assignments:
                    db.refresh(assignment)
            except Exception as e:
                db.rollback()
                raise ValueError(f"Failed to save assignments: {str(e)}")
        
        # If no assignments were created but there were errors, raise an error
        if not assignments and errors:
            raise ValueError(f"No assignments created. Errors: {'; '.join(errors)}")
        
        return assignments
    
    @staticmethod
    def get_client_active_assignment(
        db: Session,
        client_id: int,
        trainer_id: int
    ) -> Optional[ProgramAssignment]:
        """Get client's active program assignment"""
        return db.query(ProgramAssignment).filter(
            and_(
                ProgramAssignment.client_id == client_id,
                ProgramAssignment.trainer_id == trainer_id,
                ProgramAssignment.status == AssignmentStatus.ACTIVE
            )
        ).first()
