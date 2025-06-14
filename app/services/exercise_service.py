from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.program import Exercise
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate, ExerciseFilter
import json


class ExerciseService:
    
    @staticmethod
    def create_exercise(db: Session, exercise_data: ExerciseCreate, created_by: Optional[int] = None) -> Exercise:
        """Create a new exercise."""
        # Convert lists to JSON strings for storage
        muscle_groups_json = json.dumps(exercise_data.muscle_groups) if exercise_data.muscle_groups else None
        equipment_json = json.dumps(exercise_data.equipment) if exercise_data.equipment else None
        
        exercise = Exercise(
            name=exercise_data.name,
            description=exercise_data.description,
            instructions=exercise_data.instructions,
            muscle_groups=muscle_groups_json,
            equipment=equipment_json,
            difficulty_level=exercise_data.difficulty_level,
            image_url=exercise_data.image_url,
            video_url=exercise_data.video_url,
            created_by=created_by,
            is_public=exercise_data.is_public
        )
        
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        return exercise
    
    @staticmethod
    def get_exercise(db: Session, exercise_id: int) -> Optional[Exercise]:
        """Get a specific exercise by ID."""
        return db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    @staticmethod
    def get_exercises(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[ExerciseFilter] = None,
        user_id: Optional[int] = None
    ) -> List[Exercise]:
        """Get exercises with optional filtering."""
        query = db.query(Exercise)
        
        # Apply filters
        if filters:
            if filters.muscle_group:
                query = query.filter(Exercise.muscle_groups.like(f'%"{filters.muscle_group}"%'))
            
            if filters.equipment:
                query = query.filter(Exercise.equipment.like(f'%"{filters.equipment}"%'))
            
            if filters.difficulty_level:
                query = query.filter(Exercise.difficulty_level == filters.difficulty_level)
            
            if filters.search_term:
                search = f"%{filters.search_term}%"
                query = query.filter(
                    or_(
                        Exercise.name.ilike(search),
                        Exercise.description.ilike(search),
                        Exercise.instructions.ilike(search)
                    )
                )
            
            if filters.created_by_me is not None and user_id:
                if filters.created_by_me:
                    query = query.filter(Exercise.created_by == user_id)
                else:
                    query = query.filter(Exercise.created_by != user_id)
            
            if filters.is_public is not None:
                query = query.filter(Exercise.is_public == filters.is_public)
        
        # Show public exercises and user's private exercises
        if user_id:
            query = query.filter(
                or_(
                    Exercise.is_public == True,
                    Exercise.created_by == user_id
                )
            )
        else:
            query = query.filter(Exercise.is_public == True)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_exercise(
        db: Session, 
        exercise_id: int, 
        exercise_data: ExerciseUpdate, 
        user_id: Optional[int] = None
    ) -> Optional[Exercise]:
        """Update an exercise. Only creator can update private exercises."""
        exercise = ExerciseService.get_exercise(db, exercise_id)
        if not exercise:
            return None
        
        # Check permissions - only creator can modify their private exercises
        if not exercise.is_public and exercise.created_by != user_id:
            return None
        
        # Update fields that were provided
        update_data = exercise_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ["muscle_groups", "equipment"] and value is not None:
                # Convert lists to JSON strings for storage
                value = json.dumps(value)
            
            setattr(exercise, field, value)
        
        db.commit()
        db.refresh(exercise)
        return exercise
    
    @staticmethod
    def delete_exercise(db: Session, exercise_id: int, user_id: Optional[int] = None) -> bool:
        """Delete an exercise. Only creator can delete their exercises."""
        exercise = ExerciseService.get_exercise(db, exercise_id)
        if not exercise:
            return False
        
        # Check permissions - only creator can delete their exercises
        if exercise.created_by != user_id:
            return False
        
        db.delete(exercise)
        db.commit()
        return True
    
    @staticmethod
    def get_muscle_groups(db: Session) -> List[str]:
        """Get all unique muscle groups from exercises."""
        exercises = db.query(Exercise.muscle_groups).filter(
            Exercise.muscle_groups.isnot(None)
        ).all()
        
        muscle_groups = set()
        for exercise in exercises:
            if exercise.muscle_groups:
                try:
                    groups = json.loads(exercise.muscle_groups)
                    muscle_groups.update(groups)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sorted(list(muscle_groups))
    
    @staticmethod
    def get_equipment_types(db: Session) -> List[str]:
        """Get all unique equipment types from exercises."""
        exercises = db.query(Exercise.equipment).filter(
            Exercise.equipment.isnot(None)
        ).all()
        
        equipment_types = set()
        for exercise in exercises:
            if exercise.equipment:
                try:
                    equipment = json.loads(exercise.equipment)
                    equipment_types.update(equipment)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sorted(list(equipment_types))
