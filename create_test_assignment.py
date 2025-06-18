#!/usr/bin/env python3
"""
Create a test assignment directly in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.program_assignment import ProgramAssignment, AssignmentStatus
from app.models.user import User
from app.models.client import Client
from app.models.program import Program
from datetime import datetime

def create_test_assignment():
    """Create a test assignment"""
    db = SessionLocal()
    try:
        # Find trainer
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if not trainer:
            print("Trainer not found")
            return False
        
        # Find first client and program for this trainer
        client = db.query(Client).filter(Client.trainer_id == trainer.id).first()
        program = db.query(Program).filter(Program.trainer_id == trainer.id).first()
        
        if not client:
            print("No clients found for trainer")
            return False
        
        if not program:
            print("No programs found for trainer")
            return False
        
        # Check if assignment already exists
        existing = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client.id,
            ProgramAssignment.status == AssignmentStatus.ACTIVE
        ).first()
        
        if existing:
            print(f"Client {client.first_name} {client.last_name} already has active assignment")
            return False
        
        # Create assignment
        assignment = ProgramAssignment(
            program_id=program.id,
            client_id=client.id,
            trainer_id=trainer.id,
            start_date=datetime(2025, 6, 19, 10, 0, 0),
            custom_notes="Test assignment created directly",
            status=AssignmentStatus.ACTIVE,
            completion_percentage=0,
            sessions_completed=0,
            total_sessions=12  # Default for testing
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        print(f"Created assignment ID {assignment.id}")
        print(f"Program: {program.name}")
        print(f"Client: {client.first_name} {client.last_name}")
        print(f"Status: {assignment.status}")
        
        return True
        
    except Exception as e:
        print(f"Error creating assignment: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test assignment...")
    success = create_test_assignment()
    if success:
        print("Test assignment created successfully!")
    else:
        print("Failed to create test assignment!")
