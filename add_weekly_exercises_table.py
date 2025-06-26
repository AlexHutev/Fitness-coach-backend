#!/usr/bin/env python3
"""
Add weekly exercise assignments table to support individual exercise tracking
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy import text
from app.core.database import SessionLocal, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_weekly_exercise_table():
    """Create the weekly exercise assignments table"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weekly_exercise_assignments (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        program_assignment_id INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        trainer_id INTEGER NOT NULL,
        exercise_id INTEGER NOT NULL,
        assigned_date DATE NOT NULL,
        due_date DATE,
        week_number INTEGER NOT NULL,
        day_number INTEGER NOT NULL,
        exercise_order INTEGER NOT NULL DEFAULT 1,
        sets INTEGER NOT NULL,
        reps VARCHAR(50) NOT NULL,
        weight VARCHAR(50),
        rest_seconds INTEGER,
        exercise_notes TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        completed_date DATETIME,
        actual_sets_completed INTEGER DEFAULT 0,
        completion_percentage INTEGER DEFAULT 0,
        client_feedback TEXT,
        trainer_feedback TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        FOREIGN KEY(program_assignment_id) REFERENCES program_assignments (id) ON DELETE CASCADE,
        FOREIGN KEY(client_id) REFERENCES clients (id) ON DELETE CASCADE,
        FOREIGN KEY(trainer_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
    );
    """
    
    # Create indexes for better performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_weekly_exercise_client_id ON weekly_exercise_assignments(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_weekly_exercise_due_date ON weekly_exercise_assignments(due_date);",
        "CREATE INDEX IF NOT EXISTS idx_weekly_exercise_status ON weekly_exercise_assignments(status);",
        "CREATE INDEX IF NOT EXISTS idx_weekly_exercise_assignment_id ON weekly_exercise_assignments(program_assignment_id);",
        "CREATE INDEX IF NOT EXISTS idx_weekly_exercise_week_day ON weekly_exercise_assignments(week_number, day_number);"
    ]
    
    db = SessionLocal()
    try:
        # Create the table
        db.execute(text(create_table_sql))
        logger.info("Created weekly_exercise_assignments table")
        
        # Create indexes
        for index_sql in create_indexes_sql:
            db.execute(text(index_sql))
        
        logger.info("Created indexes for weekly_exercise_assignments table")
        
        db.commit()
        logger.info("Weekly exercise assignments table migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error creating weekly exercise assignments table: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def add_sample_weekly_exercises():
    """Add sample weekly exercises for existing program assignments"""
    
    from app.models.program_assignment import ProgramAssignment
    from app.services.weekly_exercise_service import WeeklyExerciseService
    
    db = SessionLocal()
    try:
        # Get all active program assignments
        assignments = db.query(ProgramAssignment).filter(
            ProgramAssignment.status == 'active'
        ).all()
        
        logger.info(f"Found {len(assignments)} active program assignments")
        
        for assignment in assignments:
            try:
                logger.info(f"Generating weekly exercises for assignment {assignment.id}")
                weekly_exercises = WeeklyExerciseService.generate_weekly_exercises_from_assignment(
                    db, assignment
                )
                logger.info(f"Generated {len(weekly_exercises)} weekly exercises for assignment {assignment.id}")
            except Exception as e:
                logger.warning(f"Failed to generate weekly exercises for assignment {assignment.id}: {e}")
                continue
        
        logger.info("Sample weekly exercises generation completed!")
        
    except Exception as e:
        logger.error(f"Error generating sample weekly exercises: {e}")
        raise
    finally:
        db.close()


def main():
    """Main migration function"""
    logger.info("Starting weekly exercise assignments migration...")
    
    # Create the table
    create_weekly_exercise_table()
    
    # Add sample data for existing assignments
    add_sample_weekly_exercises()
    
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    main()
