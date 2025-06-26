#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.client import Client
from app.models.user import User

def test_dashboard_stats():
    """Test the dashboard stats calculation"""
    
    db = SessionLocal()
    try:
        # Get the client record
        client_user = db.query(User).filter(User.email == "iveta@gmail.com").first()
        if not client_user:
            print("Client user not found")
            return
            
        from app.services.client_account_service import ClientAccountService
        client_record = ClientAccountService.get_client_by_user_id(db, client_user.id)
        
        if not client_record:
            print("Client record not found")
            return
            
        print("Client record found:")
        print(f"  ID: {client_record.id}")
        print(f"  Name: {client_record.first_name} {client_record.last_name}")
        print(f"  Height: {client_record.height}")
        print(f"  Weight: {client_record.weight}")
        print(f"  Activity Level: {client_record.activity_level}")
        print(f"  Primary Goal: {client_record.primary_goal}")
        
        # Test profile completion calculation
        def calculate_profile_completion(client_record) -> int:
            """Calculate what percentage of the profile is completed"""
            total_fields = 9  # Removed phone_number as it's on user record
            completed_fields = 0
            
            if client_record.height: completed_fields += 1
            if client_record.weight: completed_fields += 1
            if client_record.body_fat_percentage: completed_fields += 1
            if client_record.activity_level: completed_fields += 1
            if client_record.primary_goal: completed_fields += 1
            if client_record.date_of_birth: completed_fields += 1
            if client_record.gender: completed_fields += 1
            if client_record.emergency_contact_name: completed_fields += 1
            if client_record.emergency_contact_phone: completed_fields += 1
            
            return round((completed_fields / total_fields) * 100)
        
        completion = calculate_profile_completion(client_record)
        print(f"Profile completion: {completion}%")
        
        # Test BMI calculation
        bmi = None
        if client_record.height and client_record.weight:
            height_m = client_record.height / 100
            bmi = round(client_record.weight / (height_m ** 2), 1)
            print(f"BMI: {bmi}")
        
        # Test program stats
        from app.models.program_assignment import ProgramAssignment, AssignmentStatus
        
        active_programs = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client_record.id,
            ProgramAssignment.status == AssignmentStatus.ACTIVE
        ).count()
        
        print(f"Active programs: {active_programs}")
        
        print("Dashboard stats calculation successful!")
        
    except Exception as e:
        print(f"Error in dashboard stats: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard_stats()
