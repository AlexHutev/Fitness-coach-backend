from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.exercise import (
    Exercise,
    ExerciseCreate,
    ExerciseFilter,
    ExerciseList,
    ExerciseUpdate,
)
from app.services.exercise_service import ExerciseService
from app.utils.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=Exercise, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await ExerciseService.create_exercise(db, exercise_data, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating exercise: {e}",
        )


@router.get("/", response_model=List[ExerciseList])
async def get_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    muscle_group: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    created_by_me: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = ExerciseFilter(
        muscle_group=muscle_group,
        equipment=equipment,
        difficulty_level=difficulty_level,
        search_term=search_term,
        created_by_me=created_by_me,
        is_public=is_public,
    )
    return await ExerciseService.get_exercises(
        db=db, skip=skip, limit=limit, filters=filters, user_id=current_user.id
    )


@router.get("/public", response_model=List[ExerciseList])
async def get_public_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    muscle_group: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    filters = ExerciseFilter(
        muscle_group=muscle_group,
        equipment=equipment,
        difficulty_level=difficulty_level,
        search_term=search_term,
        is_public=True,
    )
    return await ExerciseService.get_exercises(
        db=db, skip=skip, limit=limit, filters=filters, user_id=None
    )


@router.get("/muscle-groups", response_model=List[str])
async def get_muscle_groups(db: AsyncSession = Depends(get_db)):
    return await ExerciseService.get_muscle_groups(db)


@router.get("/equipment-types", response_model=List[str])
async def get_equipment_types(db: AsyncSession = Depends(get_db)):
    return await ExerciseService.get_equipment_types(db)


@router.get("/{exercise_id}", response_model=Exercise)
async def get_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = await ExerciseService.get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
        )
    if not exercise.is_public and exercise.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return exercise


@router.put("/{exercise_id}", response_model=Exercise)
async def update_exercise(
    exercise_id: int,
    exercise_update: ExerciseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = await ExerciseService.update_exercise(
        db, exercise_id, exercise_update, current_user.id
    )
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or you don't have permission to update it",
        )
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await ExerciseService.delete_exercise(db, exercise_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found or you don't have permission to delete it",
        )


@router.post("/bulk", response_model=List[ExerciseList])
async def get_exercises_by_ids(
    exercise_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch multiple exercises by their IDs (useful for program building)."""
    out = []
    for eid in exercise_ids:
        ex = await ExerciseService.get_exercise(db, eid)
        if ex and (ex.is_public or ex.created_by == current_user.id):
            out.append(ex)
    return out
