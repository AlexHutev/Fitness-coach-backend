from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from app.models.program import DifficultyLevel


# Base exercise schema
class ExerciseBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_public: bool = True


# Schema for creating an exercise
class ExerciseCreate(ExerciseBase):
    pass


# Schema for updating an exercise
class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_public: Optional[bool] = None


# Schema for reading an exercise
class Exercise(ExerciseBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schema for listing exercises (minimal info)
class ExerciseList(BaseModel):
    id: int
    name: str
    muscle_groups: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    is_public: bool

    class Config:
        from_attributes = True


# Schema for exercise search/filter
class ExerciseFilter(BaseModel):
    muscle_group: Optional[str] = None
    equipment: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    search_term: Optional[str] = None
    created_by_me: Optional[bool] = None
    is_public: Optional[bool] = None
