from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.program_assignment import AssignmentStatus


# Client Authentication Schemas
class ClientLoginRequest(BaseModel):
    email: str
    password: str


class ClientTokenResponse(BaseModel):
    access_token: str
    token_type: str
    client_id: int
    assignment_id: int
    program_name: str


class ClientCreateCredentials(BaseModel):
    client_id: int
    email: EmailStr
    password: str


# Program Assignment Schemas
class ProgramAssignmentCreate(BaseModel):
    client_id: int
    program_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    assignment_notes: Optional[str] = None
    client_access_email: Optional[EmailStr] = None
    client_password: Optional[str] = None


class ProgramAssignmentUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None
    end_date: Optional[datetime] = None
    assignment_notes: Optional[str] = None
    trainer_feedback: Optional[str] = None


class ProgramAssignmentResponse(BaseModel):
    id: int
    trainer_id: int
    client_id: int
    program_id: int
    start_date: datetime
    end_date: Optional[datetime]
    status: AssignmentStatus
    total_workouts: int
    completed_workouts: int
    last_workout_date: Optional[datetime]
    assignment_notes: Optional[str]
    trainer_feedback: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Related data
    client_name: Optional[str] = None
    program_name: Optional[str] = None

    class Config:
        from_attributes = True


# Workout Log Schemas
class ExerciseSetData(BaseModel):
    set: int
    reps: int
    weight: Optional[str] = None
    completed: bool = True
    notes: Optional[str] = None
    rest_seconds: Optional[int] = None


class ExerciseLogCreate(BaseModel):
    exercise_name: str
    exercise_id: Optional[int] = None
    exercise_order: int = 1
    planned_sets: Optional[int] = None
    planned_reps: Optional[str] = None
    planned_weight: Optional[str] = None
    planned_rest_seconds: Optional[int] = None
    actual_sets: List[ExerciseSetData] = []
    difficulty_rating: Optional[int] = None
    exercise_notes: Optional[str] = None
    form_rating: Optional[int] = None


class WorkoutLogCreate(BaseModel):
    assignment_id: int
    day_number: int
    workout_name: Optional[str] = None
    workout_date: Optional[datetime] = None
    total_duration_minutes: Optional[int] = None
    perceived_exertion: Optional[int] = None
    client_notes: Optional[str] = None
    is_completed: bool = True
    is_skipped: bool = False
    skip_reason: Optional[str] = None
    exercises: List[ExerciseLogCreate] = []


class ExerciseLogResponse(BaseModel):
    id: int
    exercise_name: str
    exercise_id: Optional[int]
    exercise_order: int
    planned_sets: Optional[int]
    planned_reps: Optional[str]
    planned_weight: Optional[str]
    planned_rest_seconds: Optional[int]
    actual_sets: List[Dict[str, Any]]
    difficulty_rating: Optional[int]
    exercise_notes: Optional[str]
    form_rating: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutLogResponse(BaseModel):
    id: int
    assignment_id: int
    client_id: int
    workout_date: datetime
    day_number: int
    workout_name: Optional[str]
    total_duration_minutes: Optional[int]
    perceived_exertion: Optional[int]
    client_notes: Optional[str]
    trainer_feedback: Optional[str]
    is_completed: bool
    is_skipped: bool
    skip_reason: Optional[str]
    exercises: List[ExerciseLogResponse]
    created_at: datetime

    class Config:
        from_attributes = True


# Client Dashboard Schemas
class ClientDashboardProgram(BaseModel):
    assignment_id: int
    program_id: int
    program_name: str
    program_description: Optional[str]
    program_type: str
    difficulty_level: str
    start_date: datetime
    end_date: Optional[datetime]
    status: AssignmentStatus
    total_workouts: int
    completed_workouts: int
    completion_percentage: float
    last_workout_date: Optional[datetime]
    next_workout_day: Optional[int]


class ClientProgressStats(BaseModel):
    total_programs: int
    active_programs: int
    completed_programs: int
    total_workouts_completed: int
    current_streak: int
    longest_streak: int
    average_workout_duration: Optional[float]
    average_perceived_exertion: Optional[float]


class ClientDashboardResponse(BaseModel):
    client_id: int
    client_name: str
    active_programs: List[ClientDashboardProgram]
    recent_workouts: List[WorkoutLogResponse]
    progress_stats: ClientProgressStats


# Workout Template Schema (for client to see what's planned)
class WorkoutExerciseTemplate(BaseModel):
    exercise_id: Optional[int]
    exercise_name: str
    sets: int
    reps: str
    weight: Optional[str]
    rest_seconds: int
    notes: Optional[str]
    muscle_groups: Optional[List[str]] = []
    equipment: Optional[List[str]] = []
    instructions: Optional[str] = None


class WorkoutDayTemplate(BaseModel):
    day: int
    name: str
    exercises: List[WorkoutExerciseTemplate]


class ProgramTemplateForClient(BaseModel):
    program_id: int
    assignment_id: int
    program_name: str
    program_description: Optional[str]
    program_type: str
    difficulty_level: str
    duration_weeks: Optional[int]
    sessions_per_week: Optional[int]
    workout_structure: List[WorkoutDayTemplate]
    trainer_notes: Optional[str]
