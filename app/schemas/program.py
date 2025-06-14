from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models.program import ProgramType, DifficultyLevel


# Exercise within a workout day
class WorkoutExercise(BaseModel):
    exercise_id: int
    sets: int = Field(gt=0, description="Number of sets")
    reps: str = Field(description="Number of reps (e.g., '10', '8-12', 'to failure')")
    weight: str = Field(description="Weight specification (e.g., 'bodyweight', '60kg', '80%')")
    rest_seconds: int = Field(ge=0, description="Rest time in seconds")
    notes: Optional[str] = None


# Workout day structure
class WorkoutDay(BaseModel):
    day: int = Field(ge=1, description="Day number in the program")
    name: str = Field(description="Name of the workout day (e.g., 'Push Day', 'Upper Body')")
    exercises: List[WorkoutExercise] = []


# Base program schema
class ProgramBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    program_type: ProgramType
    difficulty_level: DifficultyLevel
    duration_weeks: Optional[int] = Field(None, gt=0, le=52)
    sessions_per_week: Optional[int] = Field(None, gt=0, le=7)
    workout_structure: List[WorkoutDay] = []
    tags: Optional[str] = None
    equipment_needed: Optional[List[str]] = None
    is_template: bool = True


# Schema for creating a program
class ProgramCreate(ProgramBase):
    pass


# Schema for updating a program
class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    program_type: Optional[ProgramType] = None
    difficulty_level: Optional[DifficultyLevel] = None
    duration_weeks: Optional[int] = Field(None, gt=0, le=52)
    sessions_per_week: Optional[int] = Field(None, gt=0, le=7)
    workout_structure: Optional[List[WorkoutDay]] = None
    tags: Optional[str] = None
    equipment_needed: Optional[List[str]] = None
    is_template: Optional[bool] = None
    is_active: Optional[bool] = None


# Schema for reading a program
class Program(ProgramBase):
    id: int
    trainer_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema for listing programs (minimal info)
class ProgramList(BaseModel):
    id: int
    name: str
    program_type: ProgramType
    difficulty_level: DifficultyLevel
    duration_weeks: Optional[int]
    sessions_per_week: Optional[int]
    is_template: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Schema for program assignment to clients
class ProgramAssignment(BaseModel):
    program_id: int
    client_id: int
    start_date: Optional[datetime] = None
    custom_notes: Optional[str] = None
