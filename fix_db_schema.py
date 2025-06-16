#!/usr/bin/env python3
"""
Fix database schema for DifficultyLevel enum
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.program import Program
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix the database schema for DifficultyLevel enum"""
    
    try:
        # Check if we have any programs
        db = SessionLocal()
        program_count = db.query(Program).count()
        print(f"Current programs in database: {program_count}")
        db.close()
        
        if program_count == 0:
            # No programs exist, safe to recreate tables
            print("No programs found, recreating tables...")
            
            # Drop and recreate tables
            Base.metadata.drop_all(bind=engine, tables=[Program.__table__])
            Base.metadata.create_all(bind=engine, tables=[Program.__table__])
            
            print("✓ Programs table recreated successfully!")
            return True
        else:
            print("⚠️ Programs exist in database.")
            print("For safety, please backup your database before making schema changes.")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    print("=== Fixing Database Schema for DifficultyLevel ===\n")
    success = fix_database_schema()
    
    if success:
        print("\n✓ Database schema fixed successfully!")
        print("You can now create programs with enum difficulty levels.")
    else:
        print("\n❌ Schema fix failed or was skipped.")
