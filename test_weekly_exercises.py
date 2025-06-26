#!/usr/bin/env python3
"""
Test script to create sample program assignments and generate weekly exercises
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
from app.core.database import SessionLocal
from app.models.user import User
from app.models.client import Client
from app.models.program import Program
from app.models.program_assignment import ProgramAssignment
from app.services.program_assignment_service import ProgramAssignmentService
from app.schemas.program_assignment import BulkAssignmentCreate
from datetime import datetime, date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_assignment():
    """Create a test program assignment with weekly exercises"""
    db = SessionLocal()
    
    try:
        # Find the trainer
        trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if not trainer:
            logger.error("Trainer not found!")
            return
        
        # Find a client
        client = db.query(Client).filter(Client.trainer_id == trainer.id).first()
        if not client:
            logger.error("No clients found for trainer!")
            return
        
        # Find a program
        program = db.query(Program).filter(Program.trainer_id == trainer.id).first()
        if not program:
            logger.error("No programs found for trainer!")
            return
        
        logger.info(f"Found trainer: {trainer.email}")
        logger.info(f"Found client: {client.first_name} {client.last_name}")
        logger.info(f"Found program: {program.name}")
        
        # Check if assignment already exists
        existing = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client.id,
            ProgramAssignment.program_id == program.id,
            ProgramAssignment.status == 'active'
        ).first()
        
        if existing:
            logger.info(f"Assignment already exists with ID: {existing.id}")
            return existing.id
        
        # Create bulk assignment
        bulk_data = BulkAssignmentCreate(
            program_id=program.id,
            client_ids=[client.id],
            start_date=date.today(),
            custom_notes="Test assignment for weekly exercises"
        )
        
        # Create the assignment (this will automatically generate weekly exercises)
        assignments = ProgramAssignmentService.bulk_assign(db, bulk_data, trainer.id)
        
        if assignments:
            assignment = assignments[0]
            logger.info(f"✅ Created assignment with ID: {assignment.id}")
            
            # Check if weekly exercises were created
            from app.models.weekly_exercise import WeeklyExerciseAssignment
            weekly_exercises = db.query(WeeklyExerciseAssignment).filter(
                WeeklyExerciseAssignment.program_assignment_id == assignment.id
            ).all()
            
            logger.info(f"✅ Generated {len(weekly_exercises)} weekly exercise assignments")
            
            # Show some details
            for i, ex in enumerate(weekly_exercises[:5]):  # Show first 5
                logger.info(f"  Exercise {i+1}: Week {ex.week_number}, Day {ex.day_number} - Exercise ID {ex.exercise_id}")
            
            if len(weekly_exercises) > 5:
                logger.info(f"  ... and {len(weekly_exercises) - 5} more exercises")
            
            return assignment.id
        else:
            logger.error("Failed to create assignment")
            return None
        
    except Exception as e:
        logger.error(f"Error creating test assignment: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def test_weekly_exercises_api():
    """Test the weekly exercises API endpoints"""
    import requests
    
    try:
        # First login to get a token
        login_response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            json={'email': 'trainer@fitnesscoach.com', 'password': 'trainer123'}
        )
        
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.status_code}")
            return
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        logger.info("✅ Login successful")
        
        # Find a client ID
        db = SessionLocal()
        try:
            trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
            client = db.query(Client).filter(Client.trainer_id == trainer.id).first()
            
            if not client:
                logger.error("No client found for testing")
                return
            
            client_id = client.id
            logger.info(f"Testing with client ID: {client_id}")
        finally:
            db.close()
        
        # Test get current week exercises
        response = requests.get(
            f'http://localhost:8000/api/v1/weekly-exercises/client/{client_id}/current-week',
            headers=headers
        )
        
        logger.info(f"Current week exercises API: Status {response.status_code}")
        if response.status_code == 200:
            exercises = response.json()
            logger.info(f"✅ Found {len(exercises)} current week exercises")
            for i, ex in enumerate(exercises[:3]):  # Show first 3
                logger.info(f"  Exercise {i+1}: {ex.get('exercise_name', 'Unknown')} - Status: {ex.get('status', 'unknown')}")
        else:
            logger.error(f"API Error: {response.text}")
        
        # Test get weekly schedule
        response = requests.get(
            f'http://localhost:8000/api/v1/weekly-exercises/client/{client_id}/schedule',
            headers=headers
        )
        
        logger.info(f"Weekly schedule API: Status {response.status_code}")
        if response.status_code == 200:
            schedule = response.json()
            logger.info(f"✅ Weekly schedule: {schedule.get('total_exercises', 0)} total exercises, {schedule.get('completion_percentage', 0)}% complete")
            days = schedule.get('days', {})
            for day_key, day_exercises in days.items():
                logger.info(f"  {day_key}: {len(day_exercises)} exercises")
        else:
            logger.error(f"Schedule API Error: {response.text}")
        
    except Exception as e:
        logger.error(f"Error testing API: {e}")


def main():
    """Main test function"""
    logger.info("🚀 Starting weekly exercises test...")
    
    # Create test assignment
    assignment_id = create_test_assignment()
    
    if assignment_id:
        logger.info(f"✅ Assignment created: {assignment_id}")
        
        # Test API endpoints
        logger.info("🧪 Testing API endpoints...")
        test_weekly_exercises_api()
    else:
        logger.error("❌ Failed to create test assignment")
    
    logger.info("✅ Test completed!")


if __name__ == "__main__":
    main()
