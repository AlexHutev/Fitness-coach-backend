"""
Add missing columns to existing program_assignments table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_missing_columns():
    """Add missing columns to program_assignments table"""
    
    engine = create_engine(settings.database_url)
    
    print("Adding missing columns to program_assignments table...")
    
    with engine.connect() as conn:
        try:
            # Add client access credentials columns
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN client_access_email VARCHAR(255)"))
            print("[OK] Added client_access_email column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] client_access_email column already exists")
            else:
                print(f"[ERROR] Error adding client_access_email: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN client_hashed_password VARCHAR(255)"))
            print("[OK] Added client_hashed_password column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] client_hashed_password column already exists")
            else:
                print(f"[ERROR] Error adding client_hashed_password: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN assignment_notes TEXT"))
            print("[OK] Added assignment_notes column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] assignment_notes column already exists")
            else:
                print(f"[ERROR] Error adding assignment_notes: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN trainer_feedback TEXT"))
            print("[OK] Added trainer_feedback column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] trainer_feedback column already exists")
            else:
                print(f"[ERROR] Error adding trainer_feedback: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN total_workouts INTEGER DEFAULT 0"))
            print("[OK] Added total_workouts column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] total_workouts column already exists")
            else:
                print(f"[ERROR] Error adding total_workouts: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN completed_workouts INTEGER DEFAULT 0"))
            print("[OK] Added completed_workouts column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] completed_workouts column already exists")
            else:
                print(f"[ERROR] Error adding completed_workouts: {e}")
        
        try:
            conn.execute(text("ALTER TABLE program_assignments ADD COLUMN last_workout_date DATETIME"))
            print("[OK] Added last_workout_date column")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("[OK] last_workout_date column already exists")
            else:
                print(f"[ERROR] Error adding last_workout_date: {e}")
        
        conn.commit()
        print("\nDatabase schema updated successfully!")

if __name__ == "__main__":
    print("FitnessCoach - Add Missing Columns")
    print("=" * 50)
    
    try:
        add_missing_columns()
        print("\nColumn addition completed successfully!")
        
    except Exception as e:
        print(f"\nColumn addition failed: {e}")
        sys.exit(1)