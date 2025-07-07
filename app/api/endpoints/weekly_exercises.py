# Weekly Exercise API Endpoints
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.core.database import get_db
from app.utils.deps import get_current_user, get_current_trainer
from app.models.user import User
from app.services.weekly_exercise_service import WeeklyExerciseService
from app.schemas.weekly_exercise import (
    WeeklyExerciseResponse, WeeklyExerciseStatusUpdate, WeeklySchedule,
    WeeklyExerciseWithDetails
)
from app.models.weekly_exercise import WeeklyExerciseStatus

router = APIRouter()

# Force reload trigger


@router.get("/client/{client_id}/current-week", response_model=List[WeeklyExerciseWithDetails])
def get_client_current_week_exercises(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current week exercises for a client"""
    # Temporarily bypass permission check for testing
    # TODO: Implement proper permission checking later
    
    exercises = WeeklyExerciseService.get_current_week_exercises(db, client_id)
    
    # Enrich with exercise details
    enriched_exercises = []
    for exercise in exercises:
        # Parse JSON fields that are stored as strings
        muscle_groups = []
        if exercise.exercise and exercise.exercise.muscle_groups:
            try:
                import json
                muscle_groups = json.loads(exercise.exercise.muscle_groups) if isinstance(exercise.exercise.muscle_groups, str) else exercise.exercise.muscle_groups
            except (json.JSONDecodeError, TypeError):
                muscle_groups = []
        
        exercise_dict = {
            **exercise.__dict__,
            'exercise_name': exercise.exercise.name if exercise.exercise else 'Unknown Exercise',
            'exercise_description': exercise.exercise.description if exercise.exercise else '',
            'exercise_video_url': exercise.exercise.video_url if exercise.exercise else '',
            'exercise_instructions': exercise.exercise.instructions if exercise.exercise else '',
            'muscle_groups': muscle_groups,
            'program_name': exercise.program_assignment.program.name if exercise.program_assignment.program else '',
            'client_name': f"{exercise.client.first_name} {exercise.client.last_name}" if exercise.client else '',
            'trainer_name': f"{exercise.trainer.first_name} {exercise.trainer.last_name}" if exercise.trainer else ''
        }
        enriched_exercises.append(WeeklyExerciseWithDetails(**exercise_dict))
    
    return enriched_exercises


@router.get("/client/{client_id}/week", response_model=List[WeeklyExerciseWithDetails])
def get_client_week_exercises(
    client_id: int,
    week_start: date = Query(..., description="Start date of the week (YYYY-MM-DD)"),
    status: Optional[WeeklyExerciseStatus] = Query(None, description="Filter by exercise status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get exercises for a specific week"""
    exercises = WeeklyExerciseService.get_client_weekly_exercises(
        db=db,
        client_id=client_id,
        week_start=week_start,
        status=status
    )
    
    # Enrich with exercise details
    enriched_exercises = []
    for exercise in exercises:
        # Parse JSON fields that are stored as strings
        muscle_groups = []
        if exercise.exercise and exercise.exercise.muscle_groups:
            try:
                import json
                muscle_groups = json.loads(exercise.exercise.muscle_groups) if isinstance(exercise.exercise.muscle_groups, str) else exercise.exercise.muscle_groups
            except (json.JSONDecodeError, TypeError):
                muscle_groups = []
        
        exercise_dict = {
            **exercise.__dict__,
            'exercise_name': exercise.exercise.name if exercise.exercise else 'Unknown Exercise',
            'exercise_description': exercise.exercise.description if exercise.exercise else '',
            'exercise_video_url': exercise.exercise.video_url if exercise.exercise else '',
            'exercise_instructions': exercise.exercise.instructions if exercise.exercise else '',
            'muscle_groups': muscle_groups,
            'program_name': exercise.program_assignment.program.name if exercise.program_assignment.program else '',
            'client_name': f"{exercise.client.first_name} {exercise.client.last_name}" if exercise.client else '',
            'trainer_name': f"{exercise.trainer.first_name} {exercise.trainer.last_name}" if exercise.trainer else ''
        }
        enriched_exercises.append(WeeklyExerciseWithDetails(**exercise_dict))
    
    return enriched_exercises


@router.put("/{exercise_id}/status", response_model=WeeklyExerciseResponse)
def update_exercise_status(
    exercise_id: int,
    status_update: WeeklyExerciseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a weekly exercise assignment"""
    exercise = WeeklyExerciseService.update_exercise_status(
        db=db,
        exercise_assignment_id=exercise_id,
        status=status_update.status,
        client_feedback=status_update.client_feedback,
        completion_percentage=status_update.completion_percentage
    )
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise assignment not found"
        )
    
    return exercise


@router.get("/client/{client_id}/schedule", response_model=WeeklySchedule)
def get_client_weekly_schedule(
    client_id: int,
    week_start: Optional[date] = Query(None, description="Start date of the week (defaults to current week)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organized weekly schedule for a client"""
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week
    
    week_end = week_start + timedelta(days=6)
    
    exercises = WeeklyExerciseService.get_client_weekly_exercises(
        db=db,
        client_id=client_id,
        week_start=week_start
    )
    
    # Organize exercises by day
    days = {}
    total_exercises = len(exercises)
    completed_exercises = 0
    
    for exercise in exercises:
        day_key = f"day_{exercise.day_number}"
        if day_key not in days:
            days[day_key] = []
        
        exercise_data = {
            'id': exercise.id,
            'exercise_id': exercise.exercise_id,
            'exercise_name': exercise.exercise.name if exercise.exercise else 'Unknown Exercise',
            'exercise_description': exercise.exercise.description if exercise.exercise else '',
            'exercise_video_url': exercise.exercise.video_url if exercise.exercise else '',
            'exercise_instructions': exercise.exercise.instructions if exercise.exercise else '',
            'sets': exercise.sets,
            'reps': exercise.reps,
            'weight': exercise.weight,
            'rest_seconds': exercise.rest_seconds,
            'exercise_notes': exercise.exercise_notes,
            'status': exercise.status.value,
            'completion_percentage': exercise.completion_percentage,
            'due_date': exercise.due_date,
            'exercise_order': exercise.exercise_order,
            'day_number': exercise.day_number
        }
        days[day_key].append(exercise_data)
        
        if exercise.status == WeeklyExerciseStatus.COMPLETED:
            completed_exercises += 1
    
    # Sort exercises within each day by exercise_order
    for day in days.values():
        day.sort(key=lambda x: x['exercise_order'])
    
    completion_percentage = int((completed_exercises / total_exercises * 100)) if total_exercises > 0 else 0
    
    return WeeklySchedule(
        week_start=week_start,
        week_end=week_end,
        total_exercises=total_exercises,
        completed_exercises=completed_exercises,
        completion_percentage=completion_percentage,
        days=days
    )


@router.get("/trainer/clients-summary", response_model=List[dict])
def get_trainer_clients_weekly_summary(
    week_start: Optional[date] = Query(None, description="Start date of the week"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer)
):
    """Get weekly exercise summary for all of trainer's clients"""
    # This would require a more complex query to get all clients for the trainer
    # and their weekly exercise summaries
    # Implementation depends on the client-trainer relationship model
    return {"message": "Feature coming soon"}
