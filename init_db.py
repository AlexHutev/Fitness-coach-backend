#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.models.user import User, UserRole, SpecializationType, ExperienceLevel
from app.models.client import Client, Gender, ActivityLevel, GoalType
from app.models.program import Program, Exercise
from app.core.security import get_password_hash
from app.core.sample_data import seed_sample_exercises

def init_database():
    """Initialize database with tables and sample data"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")
    
    # Create session
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users == 0:
            print("Creating sample users...")
            create_sample_users(db)
        
        # Check if clients already exist
        existing_clients = db.query(Client).count()
        if existing_clients == 0:
            print("Creating sample clients...")
            create_sample_clients(db)
        
        # Seed exercises
        print("Seeding sample exercises...")
        seed_sample_exercises(db)
        
        print("Database initialization complete!")
        
    except Exception as e:
        print("Error during initialization:", e)
        db.rollback()
    finally:
        db.close()

def create_sample_users(db):
    """Create sample users"""
    sample_users = [
        {
            "email": "trainer@fitnesscoach.com",
            "first_name": "John",
            "last_name": "Doe",
            "hashed_password": get_password_hash("trainer123"),
            "role": UserRole.TRAINER,
            "specialization": SpecializationType.PERSONAL_TRAINING,
            "experience": ExperienceLevel.EXPERIENCED,
            "bio": "Experienced personal trainer specializing in strength training and weight loss.",
            "is_active": True,
            "is_verified": True
        },
        {
            "email": "admin@fitnesscoach.com",
            "first_name": "Admin",
            "last_name": "User",
            "hashed_password": get_password_hash("admin123"),
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True
        }
    ]
    
    for user_data in sample_users:
        user = User(**user_data)
        db.add(user)
    
    db.commit()
    print(f"Created {len(sample_users)} sample users!")

def create_sample_clients(db):
    """Create sample clients"""
    # Find trainer user
    trainer = db.query(User).filter(User.email == "trainer@fitnesscoach.com").first()
    if not trainer:
        print("No trainer found!")
        return
    
    sample_clients = [
        {
            "trainer_id": trainer.id,
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone_number": "+1234567890",
            "gender": Gender.MALE,
            "height": 180.0,
            "weight": 75.0,
            "activity_level": ActivityLevel.MODERATELY_ACTIVE,
            "primary_goal": GoalType.MUSCLE_GAIN,
            "is_active": True
        },
        {
            "trainer_id": trainer.id,
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@example.com",
            "phone_number": "+1234567891",
            "gender": Gender.FEMALE,
            "height": 165.0,
            "weight": 60.0,
            "activity_level": ActivityLevel.LIGHTLY_ACTIVE,
            "primary_goal": GoalType.WEIGHT_LOSS,
            "is_active": True
        },
        {
            "trainer_id": trainer.id,
            "first_name": "Mike",
            "last_name": "Davis",
            "email": "mike.davis@example.com",
            "phone_number": "+1234567892",
            "gender": Gender.MALE,
            "height": 175.0,
            "weight": 80.0,
            "activity_level": ActivityLevel.VERY_ACTIVE,
            "primary_goal": GoalType.STRENGTH,
            "is_active": True
        },
        {
            "trainer_id": trainer.id,
            "first_name": "Emily",
            "last_name": "Wilson",
            "email": "emily.wilson@example.com",
            "phone_number": "+1234567893",
            "gender": Gender.FEMALE,
            "height": 160.0,
            "weight": 55.0,
            "activity_level": ActivityLevel.SEDENTARY,
            "primary_goal": GoalType.GENERAL_FITNESS,
            "is_active": True
        },
        {
            "trainer_id": trainer.id,
            "first_name": "David",
            "last_name": "Brown",
            "email": "david.brown@example.com",
            "phone_number": "+1234567894",
            "gender": Gender.MALE,
            "height": 185.0,
            "weight": 90.0,
            "activity_level": ActivityLevel.VERY_ACTIVE,
            "primary_goal": GoalType.ENDURANCE,
            "is_active": True
        }
    ]
    
    for client_data in sample_clients:
        client = Client(**client_data)
        db.add(client)
    
    db.commit()
    print(f"Created {len(sample_clients)} sample clients!")

if __name__ == "__main__":
    init_database()
