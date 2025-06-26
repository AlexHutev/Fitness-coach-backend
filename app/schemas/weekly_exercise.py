# Weekly Exercise Schemas
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime
from app.models.weekly_exercise import WeeklyExerciseStatus


class WeeklyExerciseBase(BaseModel):
    sets: int
    reps: str
    weight: Optional[str] = None
    rest_seconds: Optional[int] = None
    exercise_notes: Optional[str] = None


class WeeklyExerciseCreate(WeeklyExerciseBase):
    program_assignment_id: int
    client_id: int
    trainer_id: int
    exercise_id: int
    assigned_date: date
    due_date: Optional[date] = None
    week_number: int
    day_number: int
    exercise_order: int = 1


class WeeklyExerciseUpdate(BaseModel):
    status: Optional[WeeklyExerciseStatus] = None
    completion_percentage: Optional[int] = None
    client_feedback: Optional[str] = None
    trainer_feedback: Optional[str] = None
    actual_sets_completed: Optional[int] = None
    
    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Completion percentage must be between 0 and 100')
        return v


class WeeklyExerciseResponse(WeeklyExerciseBase):
    id: int
    program_assignment_id: int
    client_id: int
    trainer_id: int
    exercise_id: int
    assigned_date: date
    due_date: Optional[date] = None
    week_number: int
    day_number: int
    exercise_order: int
    status: WeeklyExerciseStatus
    completed_date: Optional[datetime] = None
    actual_sets_completed: int
    completion_percentage: int
    client_feedback: Optional[str] = None
    trainer_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Include exercise details
    exercise_name: Optional[str] = None
    exercise_description: Optional[str] = None
    muscle_groups: Optional[list] = None
    
    class Config:
        from_attributes = True


class WeeklyExerciseWithDetails(WeeklyExerciseResponse):
    """Extended version with full exercise and program details"""
    program_name: Optional[str] = None
    client_name: Optional[str] = None
    trainer_name: Optional[str] = None


class WeeklyExerciseStatusUpdate(BaseModel):
    status: WeeklyExerciseStatus
    client_feedback: Optional[str] = None
    completion_percentage: Optional[int] = None
    
    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Completion percentage must be between 0 and 100')
        return v


class WeeklySchedule(BaseModel):
    """Weekly view of exercises organized by day"""
    week_start: date
    week_end: date
    total_exercises: int
    completed_exercises: int
    completion_percentage: int
    days: dict  # Day number -> List of exercises
    
    class Config:
        from_attributes = True
