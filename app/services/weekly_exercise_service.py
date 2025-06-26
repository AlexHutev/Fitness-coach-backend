# Weekly Exercise Assignment Service
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date, timedelta
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.models.program_assignment import ProgramAssignment
from app.models.program import Program
from app.schemas.weekly_exercise import WeeklyExerciseCreate, WeeklyExerciseUpdate
import logging

logger = logging.getLogger(__name__)


class WeeklyExerciseService:
    
    @staticmethod
    def generate_weekly_exercises_from_assignment(
        db: Session, 
        program_assignment: ProgramAssignment
    ) -> List[WeeklyExerciseAssignment]:
        """
        Generate weekly exercise assignments when a program is assigned to a client
        """
        try:
            # Get the program details
            program = db.query(Program).filter(Program.id == program_assignment.program_id).first()
            if not program or not program.workout_structure:
                logger.warning(f"No program or workout structure found for assignment {program_assignment.id}")
                return []
            
            weekly_exercises = []
            start_date = program_assignment.start_date.date() if program_assignment.start_date else date.today()
            
            # Calculate number of weeks based on program duration
            program_weeks = program.duration_weeks or 4
            sessions_per_week = program.sessions_per_week or len(program.workout_structure)
            
            for week in range(1, program_weeks + 1):
                for day_data in program.workout_structure:
                    day_number = day_data.get('day', 1)
                    
                    # Calculate the actual date for this workout
                    # Distribute workout days evenly throughout the week
                    days_offset = ((week - 1) * 7) + ((day_number - 1) * (7 // sessions_per_week))
                    workout_date = start_date + timedelta(days=days_offset)
                    
                    # Create assignments for each exercise in this day
                    for exercise_index, exercise_data in enumerate(day_data.get('exercises', [])):
                        weekly_exercise = WeeklyExerciseAssignment(
                            program_assignment_id=program_assignment.id,
                            client_id=program_assignment.client_id,
                            trainer_id=program_assignment.trainer_id,
                            exercise_id=exercise_data.get('exercise_id'),
                            assigned_date=date.today(),
                            due_date=workout_date,
                            week_number=week,
                            day_number=day_number,
                            exercise_order=exercise_index + 1,
                            sets=exercise_data.get('sets', 3),
                            reps=exercise_data.get('reps', '10'),
                            weight=exercise_data.get('weight', 'bodyweight'),
                            rest_seconds=exercise_data.get('rest_seconds', 60),
                            exercise_notes=exercise_data.get('notes', ''),
                            status=WeeklyExerciseStatus.PENDING
                        )
                        
                        db.add(weekly_exercise)
                        weekly_exercises.append(weekly_exercise)
            
            db.commit()
            logger.info(f"Generated {len(weekly_exercises)} weekly exercise assignments for program assignment {program_assignment.id}")
            return weekly_exercises
            
        except Exception as e:
            logger.error(f"Error generating weekly exercises: {e}")
            db.rollback()
            return []
    
    @staticmethod
    def get_client_weekly_exercises(
        db: Session,
        client_id: int,
        week_start: Optional[date] = None,
        status: Optional[WeeklyExerciseStatus] = None
    ) -> List[WeeklyExerciseAssignment]:
        """Get weekly exercises for a client"""
        query = db.query(WeeklyExerciseAssignment).filter(
            WeeklyExerciseAssignment.client_id == client_id
        )
        
        if week_start:
            week_end = week_start + timedelta(days=6)
            query = query.filter(
                WeeklyExerciseAssignment.due_date >= week_start,
                WeeklyExerciseAssignment.due_date <= week_end
            )
        
        if status:
            query = query.filter(WeeklyExerciseAssignment.status == status)
        
        return query.order_by(
            WeeklyExerciseAssignment.due_date,
            WeeklyExerciseAssignment.day_number,
            WeeklyExerciseAssignment.exercise_order
        ).all()
    
    @staticmethod
    def get_current_week_exercises(
        db: Session,
        client_id: int
    ) -> List[WeeklyExerciseAssignment]:
        """Get exercises for the current week"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week
        
        return WeeklyExerciseService.get_client_weekly_exercises(
            db=db,
            client_id=client_id,
            week_start=week_start
        )
    
    @staticmethod
    def update_exercise_status(
        db: Session,
        exercise_assignment_id: int,
        status: WeeklyExerciseStatus,
        client_feedback: Optional[str] = None,
        completion_percentage: Optional[int] = None
    ) -> Optional[WeeklyExerciseAssignment]:
        """Update the status of a weekly exercise assignment"""
        try:
            exercise = db.query(WeeklyExerciseAssignment).filter(
                WeeklyExerciseAssignment.id == exercise_assignment_id
            ).first()
            
            if not exercise:
                return None
            
            exercise.status = status
            if client_feedback:
                exercise.client_feedback = client_feedback
            if completion_percentage is not None:
                exercise.completion_percentage = completion_percentage
            
            if status == WeeklyExerciseStatus.COMPLETED:
                exercise.completed_date = func.now()
                exercise.completion_percentage = 100
            
            db.commit()
            return exercise
            
        except Exception as e:
            logger.error(f"Error updating exercise status: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def delete_weekly_exercises_for_assignment(
        db: Session,
        program_assignment_id: int
    ) -> bool:
        """Delete all weekly exercises when a program assignment is removed"""
        try:
            db.query(WeeklyExerciseAssignment).filter(
                WeeklyExerciseAssignment.program_assignment_id == program_assignment_id
            ).delete()
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting weekly exercises: {e}")
            db.rollback()
            return False
