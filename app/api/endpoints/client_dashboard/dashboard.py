from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.client_account_service import ClientAccountService
from app.utils.deps import get_current_user
from typing import Optional

router = APIRouter()


def get_current_client(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure current user is a client"""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Client role required."
        )
    return current_user


@router.get("/profile")
def get_client_profile(
    current_user: User = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get client's profile information including fitness data"""
    
    # Get client record linked to this user account
    client_record = ClientAccountService.get_client_by_user_id(db, current_user.id)
    
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )
    
    return {
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number,
        },
        "client_info": {
            "id": client_record.id,
            "height": client_record.height,
            "weight": client_record.weight,
            "body_fat_percentage": client_record.body_fat_percentage,
            "activity_level": client_record.activity_level,
            "primary_goal": client_record.primary_goal,
            "secondary_goals": client_record.secondary_goals,
            "medical_conditions": client_record.medical_conditions,
            "injuries": client_record.injuries,
            "date_of_birth": client_record.date_of_birth,
            "gender": client_record.gender,
        },
        "trainer_info": {
            "id": client_record.trainer.id,
            "name": f"{client_record.trainer.first_name} {client_record.trainer.last_name}",
            "email": client_record.trainer.email,
            "specialization": client_record.trainer.specialization,
        }
    }


@router.get("/programs")
def get_client_programs(
    current_user: User = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get all training programs assigned to this client"""
    
    client_record = ClientAccountService.get_client_by_user_id(db, current_user.id)
    
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )
    
    # TODO: Implement program assignments when Program model is ready
    # For now, return placeholder
    return {
        "assigned_programs": [],
        "message": "Program assignments will be available once training program features are implemented"
    }


@router.get("/dashboard-stats")
def get_client_dashboard_stats(
    current_user: User = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for client"""
    
    client_record = ClientAccountService.get_client_by_user_id(db, current_user.id)
    
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found"
        )
    
    # Calculate basic stats
    bmi = None
    if client_record.height and client_record.weight:
        height_m = client_record.height / 100
        bmi = round(client_record.weight / (height_m ** 2), 1)
    
    return {
        "profile_completion": {
            "percentage": calculate_profile_completion(client_record),
            "missing_fields": get_missing_profile_fields(client_record)
        },
        "health_metrics": {
            "bmi": bmi,
            "weight": client_record.weight,
            "body_fat_percentage": client_record.body_fat_percentage,
        },
        "program_stats": {
            "active_programs": 0,  # TODO: Count from Program assignments
            "completed_workouts": 0,  # TODO: Count from workout logs
            "current_streak": 0,  # TODO: Calculate from workout logs
        }
    }


def calculate_profile_completion(client_record) -> int:
    """Calculate what percentage of the profile is completed"""
    total_fields = 10
    completed_fields = 0
    
    if client_record.height: completed_fields += 1
    if client_record.weight: completed_fields += 1
    if client_record.body_fat_percentage: completed_fields += 1
    if client_record.activity_level: completed_fields += 1
    if client_record.primary_goal: completed_fields += 1
    if client_record.date_of_birth: completed_fields += 1
    if client_record.gender: completed_fields += 1
    if client_record.phone_number: completed_fields += 1
    if client_record.emergency_contact_name: completed_fields += 1
    if client_record.emergency_contact_phone: completed_fields += 1
    
    return round((completed_fields / total_fields) * 100)


def get_missing_profile_fields(client_record) -> list:
    """Get list of missing profile fields"""
    missing = []
    
    if not client_record.height: missing.append("height")
    if not client_record.weight: missing.append("weight")
    if not client_record.activity_level: missing.append("activity_level")
    if not client_record.primary_goal: missing.append("primary_goal")
    if not client_record.date_of_birth: missing.append("date_of_birth")
    if not client_record.gender: missing.append("gender")
    if not client_record.emergency_contact_name: missing.append("emergency_contact_name")
    if not client_record.emergency_contact_phone: missing.append("emergency_contact_phone")
    
    return missing
