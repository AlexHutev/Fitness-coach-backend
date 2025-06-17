#!/usr/bin/env python3
"""
Create sample programs for testing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.program import Program, ProgramType, DifficultyLevel
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_programs():
    """Create sample programs for testing"""
    db = SessionLocal()
    
    try:
        # Get the trainer user
        trainer = db.query(User).filter(
            User.email == "trainer@fitnesscoach.com"
        ).first()
        
        if not trainer:
            logger.error("Trainer not found. Please run create_sample_users.py first")
            return
        
        # Check if programs already exist
        existing_programs = db.query(Program).filter(Program.trainer_id == trainer.id).count()
        if existing_programs > 0:
            logger.info(f"Sample programs already exist ({existing_programs} found)")
            return
        
        # Create sample workout structure
        sample_workout = [
            {
                "day": 1,
                "name": "Upper Body Strength",
                "exercises": [
                    {
                        "exercise_id": 1,
                        "sets": 3,
                        "reps": "8-12",
                        "weight": "bodyweight",
                        "rest_seconds": 60,
                        "notes": "Focus on form"
                    },
                    {
                        "exercise_id": 2,
                        "sets": 3,
                        "reps": "10",
                        "weight": "60kg",
                        "rest_seconds": 90,
                        "notes": "Progressive overload"
                    }
                ]
            },
            {
                "day": 2,
                "name": "Lower Body Strength", 
                "exercises": [
                    {
                        "exercise_id": 7,
                        "sets": 4,
                        "reps": "12-15",
                        "weight": "bodyweight",
                        "rest_seconds": 45,
                        "notes": "Control the movement"
                    }
                ]
            }
        ]
        
        # Create sample programs
        sample_programs = [
            {
                "name": "Beginner Strength Training",
                "description": "A comprehensive strength training program for beginners",
                "program_type": ProgramType.STRENGTH,
                "difficulty_level": DifficultyLevel.BEGINNER,
                "duration_weeks": 8,
                "sessions_per_week": 3,
                "workout_structure": sample_workout,
                "tags": "strength,beginner,full-body",
                "equipment_needed": json.dumps(["dumbbells", "bench"]),
                "is_template": True,
                "trainer_id": trainer.id,
                "is_active": True
            },
            {
                "name": "Cardio Blast Program",
                "description": "High-intensity cardio program for weight loss",
                "program_type": ProgramType.CARDIO,
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "duration_weeks": 6,
                "sessions_per_week": 4,
                "workout_structure": sample_workout,
                "tags": "cardio,weight-loss,hiit",
                "equipment_needed": json.dumps(["none"]),
                "is_template": True,
                "trainer_id": trainer.id,
                "is_active": True
            },
            {
                "name": "Advanced Powerlifting",
                "description": "Advanced powerlifting program for experienced lifters",
                "program_type": ProgramType.STRENGTH,
                "difficulty_level": DifficultyLevel.ADVANCED,
                "duration_weeks": 12,
                "sessions_per_week": 4,
                "workout_structure": sample_workout,
                "tags": "powerlifting,advanced,strength",
                "equipment_needed": json.dumps(["barbell", "plates", "rack"]),
                "is_template": True,
                "trainer_id": trainer.id,
                "is_active": True
            }
        ]
        
        # Create program objects
        for program_data in sample_programs:
            program = Program(**program_data)
            db.add(program)
        
        db.commit()
        
        logger.info(f"Successfully created {len(sample_programs)} sample programs!")
        for program_data in sample_programs:
            logger.info(f"  - {program_data['name']} ({program_data['program_type'].value})")
        
    except Exception as e:
        logger.error(f"Error creating sample programs: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_programs()
