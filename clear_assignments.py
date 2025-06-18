#!/usr/bin/env python3
"""
Clear existing assignments to test new functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.program_assignment import ProgramAssignment

def clear_assignments():
    """Clear all existing assignments"""
    db = SessionLocal()
    try:
        # Delete all assignments
        deleted_count = db.query(ProgramAssignment).delete()
        db.commit()
        print(f"Cleared {deleted_count} existing assignments")
        return True
    except Exception as e:
        print(f"Error clearing assignments: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Clearing existing assignments...")
    success = clear_assignments()
    if success:
        print("Successfully cleared assignments!")
    else:
        print("Failed to clear assignments!")
