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
    
    # Get program assignments for this client
    from app.models.program_assignment import ProgramAssignment, AssignmentStatus
    from app.models.program import Program
    from sqlalchemy.orm import joinedload
    
    assignments = db.query(ProgramAssignment).options(
        joinedload(ProgramAssignment.program),
        joinedload(ProgramAssignment.trainer)
    ).filter(
        ProgramAssignment.client_id == client_record.id,
        ProgramAssignment.status == AssignmentStatus.ACTIVE
    ).all()
    
    assigned_programs = []
    for assignment in assignments:
        program_data = {
            "assignment_id": assignment.id,
            "program_id": assignment.program_id,
            "program_name": assignment.program.name,
            "program_description": assignment.program.description,
            "program_type": assignment.program.program_type,
            "difficulty_level": assignment.program.difficulty_level,
            "duration_weeks": assignment.program.duration_weeks,
            "workout_structure": assignment.program.workout_structure,
            "assigned_date": assignment.assigned_date.isoformat() if assignment.assigned_date else None,
            "start_date": assignment.start_date.isoformat() if assignment.start_date else None,
            "end_date": assignment.end_date.isoformat() if assignment.end_date else None,
            "status": assignment.status.value,
            "completion_percentage": assignment.completion_percentage,
            "sessions_completed": assignment.sessions_completed,
            "total_sessions": assignment.total_sessions,
            "custom_notes": assignment.custom_notes,
            "trainer_notes": assignment.trainer_notes,
            "trainer_info": {
                "id": assignment.trainer.id,
                "name": f"{assignment.trainer.first_name} {assignment.trainer.last_name}",
                "email": assignment.trainer.email,
                "specialization": assignment.trainer.specialization
            }
        }
        assigned_programs.append(program_data)
    
    return {
        "assigned_programs": assigned_programs,
        "total_assignments": len(assigned_programs)
    }


@router.get("/dashboard-stats")
def get_client_dashboard_stats(
    current_user: User = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for client"""
    
    try:
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
        
        # Get program statistics
        from app.models.program_assignment import ProgramAssignment, AssignmentStatus
        
        active_programs = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client_record.id,
            ProgramAssignment.status == AssignmentStatus.ACTIVE
        ).count()
        
        # Get total completed workouts from all assignments
        try:
            total_completed_workouts = db.query(ProgramAssignment).filter(
                ProgramAssignment.client_id == client_record.id
            ).with_entities(
                db.func.sum(ProgramAssignment.completed_workouts)
            ).scalar() or 0
        except:
            total_completed_workouts = 0
        
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
                "active_programs": active_programs,
                "completed_workouts": total_completed_workouts,
                "current_streak": 0,  # TODO: Calculate from workout logs when implemented
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a basic response
        print(f"Dashboard stats error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating dashboard stats: {str(e)}"
        )


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
