from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.services.exercise_service import ExerciseService
from app.schemas.exercise import (
    ExerciseCreate, ExerciseUpdate, Exercise, ExerciseList, ExerciseFilter
)

router = APIRouter()


@router.post("/", response_model=Exercise, status_code=status.HTTP_201_CREATED)
def create_exercise(
    exercise_data: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new exercise"""
    try:
        exercise = ExerciseService.create_exercise(db, exercise_data, current_user.id)
        return exercise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating exercise: {str(e)}"
        )


@router.get("/", response_model=List[ExerciseList])
def get_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    muscle_group: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    created_by_me: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get exercises with optional filtering"""
    filters = ExerciseFilter(
        muscle_group=muscle_group,
        equipment=equipment,
        difficulty_level=difficulty_level,
        search_term=search_term,
        created_by_me=created_by_me,
        is_public=is_public
    )
    
    exercises = ExerciseService.get_exercises(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user_id=current_user.id
    )
    return exercises
@router.get("/public", response_model=List[ExerciseList])
def get_public_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    muscle_group: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get public exercises (no authentication required)"""
    filters = ExerciseFilter(
        muscle_group=muscle_group,
        equipment=equipment,
        difficulty_level=difficulty_level,
        search_term=search_term,
        is_public=True
    )
    
    exercises = ExerciseService.get_exercises(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user_id=None
    )
    return exercises


@router.get("/muscle-groups", response_model=List[str])
def get_muscle_groups(db: Session = Depends(get_db)):
    """Get all available muscle groups"""
    return ExerciseService.get_muscle_groups(db)


@router.get("/equipment-types", response_model=List[str])
def get_equipment_types(db: Session = Depends(get_db)):
    """Get all available equipment types"""
    return ExerciseService.get_equipment_types(db)


@router.get("/{exercise_id}", response_model=Exercise)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific exercise by ID"""
    exercise = ExerciseService.get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Check if user can access this exercise
    if not exercise.is_public and exercise.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return exercise


@router.put("/{exercise_id}", response_model=Exercise)
def update_exercise(
    exercise_id: int,
    exercise_update: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing exercise"""
    exercise = ExerciseService.update_exercise(db, exercise_id, exercise_update, current_user.id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or you don't have permission to update it"
        )
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an exercise"""
    success = ExerciseService.delete_exercise(db, exercise_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or you don't have permission to delete it"
        )


@router.post("/bulk", response_model=List[ExerciseList])
def get_exercises_by_ids(
    exercise_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get multiple exercises by their IDs (useful for program building)"""
    exercises = []
    for exercise_id in exercise_ids:
        exercise = ExerciseService.get_exercise(db, exercise_id)
        if exercise and (exercise.is_public or exercise.created_by == current_user.id):
            exercises.append(exercise)
    return exercises
