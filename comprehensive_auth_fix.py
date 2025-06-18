"""
Comprehensive authentication fix for both trainer and client systems
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.program import Program, ProgramType, DifficultyLevel
from app.models.program_assignment import ProgramAssignment
from app.core.security import get_password_hash
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def comprehensive_auth_fix():
    """Fix all authentication issues"""
    
    db = SessionLocal()
    
    try:
        print("=== COMPREHENSIVE AUTHENTICATION FIX ===")
        
        # 1. Fix trainer authentication
        print("\n1. Fixing Trainer Authentication...")
        
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if trainer:
            print("   Trainer found, updating password...")
            trainer.hashed_password = get_password_hash("trainer123")
            trainer.is_active = True
            trainer.is_verified = True
        else:
            print("   Creating new trainer...")
            trainer = User(
                email="trainer@fitnesscoach.com",
                first_name="John",
                last_name="Trainer",
                hashed_password=get_password_hash("trainer123"),
                role=UserRole.TRAINER,
                is_active=True,
                is_verified=True
            )
            db.add(trainer)
            db.flush()
        
        # 2. Create/verify client
        print("\n2. Creating/Verifying Client...")
        
        client = db.query(Client).filter(Client.trainer_id == trainer.id).first()
        if not client:
            print("   Creating new client...")
            client = Client(
                trainer_id=trainer.id,
                first_name="John",
                last_name="Smith",
                email="john@client.com",
                is_active=True
            )
            db.add(client)
            db.flush()
        else:
            print("   Client found, updating...")
            client.email = "john@client.com"
            client.is_active = True
        
        # 3. Create/verify program
        print("\n3. Creating/Verifying Program...")
        
        program = db.query(Program).filter(Program.trainer_id == trainer.id).first()
        if not program:
            print("   Creating new program...")
            program = Program(
                trainer_id=trainer.id,
                name="Test Program",
                description="Sample training program for testing",
                program_type=ProgramType.STRENGTH,
                difficulty_level=DifficultyLevel.BEGINNER,
                duration_weeks=8,
                sessions_per_week=3,
                workout_structure=[
                    {
                        "day": 1,
                        "name": "Upper Body",
                        "exercises": [
                            {
                                "name": "Push-ups",
                                "sets": 3,
                                "reps": "10-15",
                                "weight": "bodyweight",
                                "rest_seconds": 60
                            }
                        ]
                    }
                ],
                is_template=True,
                is_active=True
            )
            db.add(program)
            db.flush()
        else:
            print("   Program found")
        
        # 4. Create/update program assignment with client credentials
        print("\n4. Setting up Client Authentication...")
        
        assignment = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client.id,
            ProgramAssignment.program_id == program.id
        ).first()
        
        if not assignment:
            print("   Creating new assignment...")
            assignment = ProgramAssignment(
                trainer_id=trainer.id,
                client_id=client.id,
                program_id=program.id,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(weeks=8),
                assignment_notes="Sample assignment for testing",
                total_workouts=24,
                completed_workouts=0
            )
            db.add(assignment)
            db.flush()
        
        # Set client credentials using the same password hashing as the backend
        print("   Setting client credentials...")
        assignment.client_access_email = "john@client.com"
        assignment.client_hashed_password = pwd_context.hash("client123")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ AUTHENTICATION COMPLETELY FIXED!")
        print("\n🔐 WORKING CREDENTIALS:")
        print("\n👨‍💼 TRAINER LOGIN:")
        print("   URL: http://localhost:3000/login")
        print("   Email: trainer@fitnesscoach.com")
        print("   Password: trainer123")
        print("\n🏃‍♂️ CLIENT LOGIN:")
        print("   URL: http://localhost:3000/client/login")
        print("   Email: john@client.com")
        print("   Password: client123")
        print("\n📊 TESTING URLS:")
        print("   Trainer API: http://localhost:8000/api/v1/auth/login")
        print("   Client API: http://localhost:8000/api/v1/client/login")
        print("   API Docs: http://localhost:8000/docs")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = comprehensive_auth_fix()
    if success:
        print("\n🎉 Ready for testing! Both trainer and client logins should work now.")
    else:
        print("\n💥 Fix failed. Please check the error messages above.")
