"""
Fix authentication by ensuring users exist with correct passwords
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime

def fix_authentication():
    """Ensure sample users exist with correct passwords"""
    
    db = SessionLocal()
    
    try:
        # Check if trainer exists
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        
        if trainer:
            print("Trainer exists, updating password...")
            trainer.hashed_password = get_password_hash("trainer123")
        else:
            print("Creating trainer user...")
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
        
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@fitnesscoach.com").first()
        
        if admin:
            print("Admin exists, updating password...")
            admin.hashed_password = get_password_hash("admin123")
        else:
            print("Creating admin user...")
            admin = User(
                email="admin@fitnesscoach.com",
                first_name="Admin",
                last_name="User",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin)
        
        db.commit()
        
        print("\n" + "="*50)
        print("Authentication fixed!")
        print("\nTrainer Login:")
        print("Email: trainer@fitnesscoach.com")
        print("Password: trainer123")
        print("\nAdmin Login:")
        print("Email: admin@fitnesscoach.com") 
        print("Password: admin123")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_authentication()