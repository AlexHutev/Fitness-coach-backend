#!/usr/bin/env python3
"""
Create a sample admin user for testing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole, SpecializationType, ExperienceLevel
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """Create an admin user for testing"""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == "admin@fitnesscoach.com").first()
        if existing_admin:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@fitnesscoach.com",
            first_name="Admin",
            last_name="User",
            phone_number="+1234567890",
            specialization=SpecializationType.PERSONAL_TRAINING,
            experience=ExperienceLevel.EXPERT,
            bio="System administrator and fitness expert",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("Admin user created successfully!")
        logger.info("Email: admin@fitnesscoach.com")
        logger.info("Password: admin123")
        logger.info("Please change the password after first login!")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def create_sample_trainer():
    """Create a sample trainer for testing"""
    db = SessionLocal()
    
    try:
        # Check if trainer already exists
        existing_trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
        if existing_trainer:
            logger.info("Sample trainer already exists")
            return
        
        # Create trainer user
        trainer_user = User(
            email="trainer@fitnesscoach.com",
            first_name="John",
            last_name="Doe",
            phone_number="+1234567891",
            specialization=SpecializationType.STRENGTH_CONDITIONING,
            experience=ExperienceLevel.EXPERIENCED,
            bio="Experienced personal trainer specializing in strength and conditioning",
            hashed_password=get_password_hash("trainer123"),
            role=UserRole.TRAINER,
            is_active=True,
            is_verified=True
        )
        
        db.add(trainer_user)
        db.commit()
        db.refresh(trainer_user)
        
        logger.info("Sample trainer created successfully!")
        logger.info("Email: trainer@fitnesscoach.com")
        logger.info("Password: trainer123")
        
    except Exception as e:
        logger.error(f"Error creating sample trainer: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function"""
    logger.info("Creating sample users...")
    
    create_admin_user()
    create_sample_trainer()
    
    logger.info("Sample users created successfully!")


if __name__ == "__main__":
    main()
