import json
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import Exercise
from app.schemas.exercise import ExerciseCreate, ExerciseFilter, ExerciseUpdate


class ExerciseService:
    @staticmethod
    async def create_exercise(
        db: AsyncSession, exercise_data: ExerciseCreate, created_by: Optional[int] = None
    ) -> Exercise:
        muscle_groups_json = (
            json.dumps(exercise_data.muscle_groups) if exercise_data.muscle_groups else None
        )
        equipment_json = (
            json.dumps(exercise_data.equipment) if exercise_data.equipment else None
        )
        difficulty_level_str = (
            exercise_data.difficulty_level.value if exercise_data.difficulty_level else None
        )

        exercise = Exercise(
            name=exercise_data.name,
            description=exercise_data.description,
            instructions=exercise_data.instructions,
            muscle_groups=muscle_groups_json,
            equipment=equipment_json,
            difficulty_level=difficulty_level_str,
            image_url=exercise_data.image_url,
            video_url=exercise_data.video_url,
            created_by=created_by,
            is_public=exercise_data.is_public,
        )

        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        return exercise

    @staticmethod
    async def get_exercise(db: AsyncSession, exercise_id: int) -> Optional[Exercise]:
        result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_exercises(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[ExerciseFilter] = None,
        user_id: Optional[int] = None,
    ) -> List[Exercise]:
        stmt = select(Exercise)

        if filters:
            if filters.muscle_group:
                stmt = stmt.where(Exercise.muscle_groups.like(f'%"{filters.muscle_group}"%'))
            if filters.equipment:
                stmt = stmt.where(Exercise.equipment.like(f'%"{filters.equipment}"%'))
            if filters.difficulty_level:
                stmt = stmt.where(Exercise.difficulty_level == filters.difficulty_level)
            if filters.search_term:
                search = f"%{filters.search_term}%"
                stmt = stmt.where(
                    or_(
                        Exercise.name.ilike(search),
                        Exercise.description.ilike(search),
                        Exercise.instructions.ilike(search),
                    )
                )
            if filters.created_by_me is not None and user_id:
                if filters.created_by_me:
                    stmt = stmt.where(Exercise.created_by == user_id)
                else:
                    stmt = stmt.where(Exercise.created_by != user_id)
            if filters.is_public is not None:
                stmt = stmt.where(Exercise.is_public == filters.is_public)

        if user_id:
            stmt = stmt.where(
                or_(Exercise.is_public.is_(True), Exercise.created_by == user_id)
            )
        else:
            stmt = stmt.where(Exercise.is_public.is_(True))

        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update_exercise(
        db: AsyncSession,
        exercise_id: int,
        exercise_data: ExerciseUpdate,
        user_id: Optional[int] = None,
    ) -> Optional[Exercise]:
        exercise = await ExerciseService.get_exercise(db, exercise_id)
        if not exercise:
            return None
        if not exercise.is_public and exercise.created_by != user_id:
            return None

        for field, value in exercise_data.dict(exclude_unset=True).items():
            if field in ("muscle_groups", "equipment") and value is not None:
                value = json.dumps(value)
            elif field == "difficulty_level" and value is not None:
                value = value.value if hasattr(value, "value") else value
            setattr(exercise, field, value)

        await db.commit()
        await db.refresh(exercise)
        return exercise

    @staticmethod
    async def delete_exercise(
        db: AsyncSession, exercise_id: int, user_id: Optional[int] = None
    ) -> bool:
        exercise = await ExerciseService.get_exercise(db, exercise_id)
        if not exercise or exercise.created_by != user_id:
            return False
        await db.delete(exercise)
        await db.commit()
        return True

    @staticmethod
    async def get_muscle_groups(db: AsyncSession) -> List[str]:
        result = await db.execute(
            select(Exercise.muscle_groups).where(Exercise.muscle_groups.isnot(None))
        )
        muscle_groups: set[str] = set()
        for (raw,) in result.all():
            try:
                if raw:
                    muscle_groups.update(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                continue
        return sorted(muscle_groups)

    @staticmethod
    async def get_equipment_types(db: AsyncSession) -> List[str]:
        result = await db.execute(
            select(Exercise.equipment).where(Exercise.equipment.isnot(None))
        )
        equipment_types: set[str] = set()
        for (raw,) in result.all():
            try:
                if raw:
                    equipment_types.update(json.loads(raw))
            except (json.JSONDecodeError, TypeError):
                continue
        return sorted(equipment_types)
