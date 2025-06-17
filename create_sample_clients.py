#!/usr/bin/env python3
"""
Create sample clients for testing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.client import Client, Gender, ActivityLevel, GoalType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_clients():
    """Create sample clients for testing"""
    db = SessionLocal()
    
    try:
        # Get the trainer user
        trainer = db.query(User).filter(
            User.email == "trainer@fitnesscoach.com"
        ).first()
        
        if not trainer:
            logger.error("Trainer not found. Please run create_sample_users.py first")
            return
        
        # Check if clients already exist
        existing_clients = db.query(Client).filter(Client.trainer_id == trainer.id).count()
        if existing_clients > 0:
            logger.info(f"Sample clients already exist ({existing_clients} found)")
            return
        
        # Create sample clients
        sample_clients = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "phone_number": "+1 (555) 123-4567",
                "gender": Gender.MALE,
                "height": 180,  # cm
                "weight": 75.5,  # kg
                "activity_level": ActivityLevel.MODERATELY_ACTIVE,
                "primary_goal": GoalType.MUSCLE_GAIN,
                "secondary_goals": "Improve overall strength and endurance",
                "trainer_id": trainer.id,
                "is_active": True
            },
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.j@example.com",
                "phone_number": "+1 (555) 987-6543",
                "gender": Gender.FEMALE,
                "height": 165,  # cm
                "weight": 62.0,  # kg
                "activity_level": ActivityLevel.LIGHTLY_ACTIVE,
                "primary_goal": GoalType.WEIGHT_LOSS,
                "secondary_goals": "Improve cardiovascular health",
                "trainer_id": trainer.id,
                "is_active": True
            },
            {
                "first_name": "Mike",
                "last_name": "Davis",
                "email": "mike.davis@example.com",
                "phone_number": "+1 (555) 456-7890",
                "gender": Gender.MALE,
                "height": 175,  # cm
                "weight": 85.0,  # kg
                "activity_level": ActivityLevel.VERY_ACTIVE,
                "primary_goal": GoalType.STRENGTH,
                "secondary_goals": "Prepare for powerlifting competition",
                "trainer_id": trainer.id,
                "is_active": True
            }
        ]
        
        # Create client objects
        for client_data in sample_clients:
            client = Client(**client_data)
            db.add(client)
        
        db.commit()
        
        logger.info(f"Successfully created {len(sample_clients)} sample clients!")
        for client_data in sample_clients:
            logger.info(f"  - {client_data['first_name']} {client_data['last_name']} ({client_data['email']})")
        
    except Exception as e:
        logger.error(f"Error creating sample clients: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_clients()
