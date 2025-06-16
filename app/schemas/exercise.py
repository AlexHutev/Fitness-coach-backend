from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
import json
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

    @validator('muscle_groups', pre=True)
    def parse_muscle_groups(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    @validator('equipment', pre=True)
    def parse_equipment(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

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

    @validator('muscle_groups', pre=True)
    def parse_muscle_groups(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    @validator('equipment', pre=True)
    def parse_equipment(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

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
