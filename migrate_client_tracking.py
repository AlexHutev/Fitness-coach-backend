"""
Database migration script to add client tracking tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base, SessionLocal
from app.models import *  # Import all models

def create_new_tables():
    """Create the new tables for client tracking"""
    
    engine = create_engine(settings.database_url)
    
    print("Creating new tables for client tracking...")
    
    # Create all tables (will only create new ones)
    Base.metadata.create_all(bind=engine)
    
    print("Tables created successfully!")
    
    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]
        
        print("\nExisting tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Check if our new tables were created
        new_tables = ['program_assignments', 'workout_logs', 'exercise_logs']
        for table in new_tables:
            if table in tables:
                print(f"[OK] {table} table created successfully")
            else:
                print(f"[ERROR] {table} table not found")

def add_sample_assignments():
    """Add sample program assignments for testing"""
    
    db = SessionLocal()
    
    try:
        # Check if we have users and clients
        from app.models import User, Client, Program, ProgramAssignment
        from app.services.client_auth_service import client_auth_service
        from datetime import datetime, timedelta
        
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if not trainer:
            print("No trainer found. Please run the user setup script first.")
            return
        
        clients = db.query(Client).filter(Client.trainer_id == trainer.id).all()
        if not clients:
            print("No clients found. Please create some clients first.")
            return
        
        programs = db.query(Program).filter(Program.trainer_id == trainer.id).all()
        if not programs:
            print("No programs found. Please create some programs first.")
            return
        
        # Create sample assignments
        for i, client in enumerate(clients[:2]):  # Assign to first 2 clients
            if i < len(programs):
                program = programs[i]
                
                # Check if assignment already exists
                existing = db.query(ProgramAssignment).filter(
                    ProgramAssignment.client_id == client.id,
                    ProgramAssignment.program_id == program.id
                ).first()
                
                if existing:
                    print(f"Assignment already exists for client {client.first_name}")
                    continue
                
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
                
                # Set up client credentials
                client_email = f"{client.first_name.lower()}@client.com"
                client_password = "client123"
                
                success = client_auth_service.create_client_credentials(
                    db, assignment.id, client_email, client_password
                )
                
                if success:
                    print(f"[OK] Created assignment for {client.first_name} {client.last_name}")
                    print(f"   Client login: {client_email} / {client_password}")
                else:
                    print(f"[ERROR] Failed to create credentials for {client.first_name}")
        
        db.commit()
        print("\nSample assignments created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating sample assignments: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("FitnessCoach - Client Tracking Migration")
    print("=" * 50)
    
    try:
        create_new_tables()
        print("\n" + "=" * 50)
        add_sample_assignments()
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("\nClient login credentials created:")
        print("Email format: [firstname]@client.com")
        print("Password: client123")
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)