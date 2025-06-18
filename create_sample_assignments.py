"""
Create sample client assignments with credentials for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models import User, Client, Program, ProgramAssignment
from app.services.client_auth_service import client_auth_service
from datetime import datetime, timedelta

def create_sample_client_assignments():
    """Create sample assignments with client credentials"""
    
    db = SessionLocal()
    
    try:
        # Get trainer
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if not trainer:
            print("No trainer found. Please run the setup script first.")
            return
        
        # Get clients
        clients = db.query(Client).filter(Client.trainer_id == trainer.id).all()
        if not clients:
            print("No clients found. Please create some clients first.")
            return
        
        # Get programs
        programs = db.query(Program).filter(Program.trainer_id == trainer.id).all()
        if not programs:
            print("No programs found. Please create some programs first.")
            return
        
        print(f"Found {len(clients)} clients and {len(programs)} programs")
        
        # Create assignments for each client
        for i, client in enumerate(clients):
            if i < len(programs):
                program = programs[i % len(programs)]  # Cycle through programs
                
                # Check if assignment already exists
                existing = db.query(ProgramAssignment).filter(
                    ProgramAssignment.client_id == client.id,
                    ProgramAssignment.program_id == program.id
                ).first()
                
                if existing:
                    print(f"Assignment already exists for {client.first_name} - updating credentials")
                    assignment = existing
                else:
                    # Create new assignment
                    assignment = ProgramAssignment(
                        trainer_id=trainer.id,
                        client_id=client.id,
                        program_id=program.id,
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(weeks=8),
                        assignment_notes=f"Sample assignment for {client.first_name}",
                        total_workouts=24  # 8 weeks × 3 workouts per week
                    )
                    
                    db.add(assignment)
                    db.flush()
                    print(f"Created assignment for {client.first_name} {client.last_name}")
                
                # Set up client credentials
                client_email = f"{client.first_name.lower()}@client.com"
                client_password = "client123"
                
                success = client_auth_service.create_client_credentials(
                    db, assignment.id, client_email, client_password
                )
                
                if success:
                    print(f"[OK] Set up credentials for {client.first_name}")
                    print(f"   Login: {client_email} / {client_password}")
                else:
                    print(f"[ERROR] Failed to set up credentials for {client.first_name}")
        
        db.commit()
        print("\n" + "="*60)
        print("Sample client assignments created successfully!")
        print("\nClient Login Credentials:")
        print("=" * 30)
        
        # List all clients with credentials
        assignments_with_creds = db.query(ProgramAssignment).filter(
            ProgramAssignment.trainer_id == trainer.id,
            ProgramAssignment.client_access_email.isnot(None)
        ).all()
        
        for assignment in assignments_with_creds:
            client = db.query(Client).filter(Client.id == assignment.client_id).first()
            program = db.query(Program).filter(Program.id == assignment.program_id).first()
            print(f"Client: {client.first_name} {client.last_name}")
            print(f"Email: {assignment.client_access_email}")
            print(f"Password: client123")
            print(f"Program: {program.name}")
            print("-" * 30)
        
        print("\nYou can now test the client login at: http://localhost:3000/client/login")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating assignments: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_client_assignments()