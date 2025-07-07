#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.client import Client, Gender, ActivityLevel, GoalType

def main():
    db = SessionLocal()
    
    try:
        print("=== USERS ===")
        users = db.query(User).all()
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Role: {user.role}, Name: {user.first_name} {user.last_name}")
        
        print("\n=== CLIENTS ===")
        clients = db.query(Client).all()
        for client in clients:
            print(f"ID: {client.id}, Name: {client.first_name} {client.last_name}, Trainer ID: {client.trainer_id}, Active: {client.is_active}")
        
        # If no clients exist, create some sample clients
        if len(clients) == 0:
            print("\nNo clients found. Creating sample clients...")
            create_sample_clients(db)
        
    finally:
        db.close()

def create_sample_clients(db):
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
        }
    ]
    
    for client_data in sample_clients:
        client = Client(**client_data)
        db.add(client)
    
    db.commit()
    print(f"Created {len(sample_clients)} sample clients!")

if __name__ == "__main__":
    main()
