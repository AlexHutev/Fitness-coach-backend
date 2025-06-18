from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import WorkoutLog, ExerciseLog, ProgramAssignment
from app.schemas.client_schemas import (
    WorkoutLogCreate, WorkoutLogResponse, ExerciseLogResponse,
    ExerciseLogCreate, ExerciseSetData
)


class WorkoutTrackingService:
    
    def create_workout_log(self, db: Session, workout_data: WorkoutLogCreate, client_id: int) -> Optional[WorkoutLogResponse]:
        """Create a new workout log with exercise logs"""
        
        # Verify assignment belongs to client
        assignment = db.query(ProgramAssignment).filter(
            ProgramAssignment.id == workout_data.assignment_id,
            ProgramAssignment.client_id == client_id
        ).first()
        
        if not assignment:
            return None
        
        # Create workout log
        workout_log = WorkoutLog(
            assignment_id=workout_data.assignment_id,
            client_id=client_id,
            workout_date=workout_data.workout_date or datetime.now(),
            day_number=workout_data.day_number,
            workout_name=workout_data.workout_name,
            total_duration_minutes=workout_data.total_duration_minutes,
            perceived_exertion=workout_data.perceived_exertion,
            client_notes=workout_data.client_notes,
            is_completed=workout_data.is_completed,
            is_skipped=workout_data.is_skipped,
            skip_reason=workout_data.skip_reason
        )
        
        db.add(workout_log)
        db.flush()  # Get the ID without committing
        
        # Create exercise logs
        exercise_logs = []
        for exercise_data in workout_data.exercises:
            exercise_log = ExerciseLog(
                workout_log_id=workout_log.id,
                exercise_id=exercise_data.exercise_id,
                exercise_name=exercise_data.exercise_name,
                exercise_order=exercise_data.exercise_order,
                planned_sets=exercise_data.planned_sets,
                planned_reps=exercise_data.planned_reps,
                planned_weight=exercise_data.planned_weight,
                planned_rest_seconds=exercise_data.planned_rest_seconds,
                actual_sets=[set_data.dict() for set_data in exercise_data.actual_sets],
                difficulty_rating=exercise_data.difficulty_rating,
                exercise_notes=exercise_data.exercise_notes,
                form_rating=exercise_data.form_rating
            )
            db.add(exercise_log)
            exercise_logs.append(exercise_log)
        
        # Update assignment progress
        if workout_data.is_completed:
            assignment.completed_workouts += 1
            assignment.last_workout_date = workout_log.workout_date
        
        db.commit()
        db.refresh(workout_log)
        
        # Return formatted response
        return self._format_workout_response(workout_log, exercise_logs)
    
    def get_workout_log(self, db: Session, workout_id: int, client_id: int) -> Optional[WorkoutLogResponse]:
        """Get a specific workout log"""
        workout_log = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.id == workout_id, WorkoutLog.client_id == client_id)
            .options(joinedload(WorkoutLog.exercise_logs))
            .first()
        )
        
        if not workout_log:
            return None
        
        return self._format_workout_response(workout_log, workout_log.exercise_logs)
    
    def get_workout_logs_for_assignment(
        self, 
        db: Session, 
        assignment_id: int, 
        client_id: int,
        limit: int = 50
    ) -> List[WorkoutLogResponse]:
        """Get all workout logs for a specific assignment"""
        
        # Verify assignment belongs to client
        assignment = db.query(ProgramAssignment).filter(
            ProgramAssignment.id == assignment_id,
            ProgramAssignment.client_id == client_id
        ).first()
        
        if not assignment:
            return []
        
        workout_logs = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.assignment_id == assignment_id)
            .options(joinedload(WorkoutLog.exercise_logs))
            .order_by(WorkoutLog.workout_date.desc())
            .limit(limit)
            .all()
        )
        
        return [
            self._format_workout_response(log, log.exercise_logs)
            for log in workout_logs
        ]
    
    def update_workout_log(
        self, 
        db: Session, 
        workout_id: int, 
        client_id: int,
        update_data: dict
    ) -> Optional[WorkoutLogResponse]:
        """Update an existing workout log"""
        
        workout_log = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.id == workout_id, WorkoutLog.client_id == client_id)
            .first()
        )
        
        if not workout_log:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'total_duration_minutes', 'perceived_exertion', 'client_notes', 
            'is_completed', 'is_skipped', 'skip_reason'
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(workout_log, field):
                setattr(workout_log, field, value)
        
        db.commit()
        db.refresh(workout_log)
        
        # Get updated workout with exercise logs
        workout_log = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.id == workout_id)
            .options(joinedload(WorkoutLog.exercise_logs))
            .first()
        )
        
        return self._format_workout_response(workout_log, workout_log.exercise_logs)
    
    def update_exercise_log(
        self,
        db: Session,
        exercise_log_id: int,
        client_id: int,
        update_data: dict
    ) -> Optional[ExerciseLogResponse]:
        """Update an exercise log within a workout"""
        
        exercise_log = (
            db.query(ExerciseLog)
            .join(WorkoutLog)
            .filter(
                ExerciseLog.id == exercise_log_id,
                WorkoutLog.client_id == client_id
            )
            .first()
        )
        
        if not exercise_log:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'actual_sets', 'difficulty_rating', 'exercise_notes', 'form_rating'
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(exercise_log, field):
                setattr(exercise_log, field, value)
        
        db.commit()
        db.refresh(exercise_log)
        
        return ExerciseLogResponse(
            id=exercise_log.id,
            exercise_name=exercise_log.exercise_name,
            exercise_id=exercise_log.exercise_id,
            exercise_order=exercise_log.exercise_order,
            planned_sets=exercise_log.planned_sets,
            planned_reps=exercise_log.planned_reps,
            planned_weight=exercise_log.planned_weight,
            planned_rest_seconds=exercise_log.planned_rest_seconds,
            actual_sets=exercise_log.actual_sets or [],
            difficulty_rating=exercise_log.difficulty_rating,
            exercise_notes=exercise_log.exercise_notes,
            form_rating=exercise_log.form_rating,
            created_at=exercise_log.created_at
        )
    
    def get_workout_history_summary(
        self, 
        db: Session, 
        assignment_id: int, 
        client_id: int
    ) -> dict:
        """Get summary statistics for workout history"""
        
        # Verify assignment belongs to client
        assignment = db.query(ProgramAssignment).filter(
            ProgramAssignment.id == assignment_id,
            ProgramAssignment.client_id == client_id
        ).first()
        
        if not assignment:
            return {}
        
        # Get workout statistics
        workout_stats = (
            db.query(
                func.count(WorkoutLog.id).label('total_workouts'),
                func.count(func.nullif(WorkoutLog.is_completed, False)).label('completed_workouts'),
                func.count(func.nullif(WorkoutLog.is_skipped, False)).label('skipped_workouts'),
                func.avg(WorkoutLog.total_duration_minutes).label('avg_duration'),
                func.avg(WorkoutLog.perceived_exertion).label('avg_exertion')
            )
            .filter(WorkoutLog.assignment_id == assignment_id)
            .first()
        )
        
        return {
            'total_workouts': workout_stats.total_workouts or 0,
            'completed_workouts': workout_stats.completed_workouts or 0,
            'skipped_workouts': workout_stats.skipped_workouts or 0,
            'completion_rate': round(
                (workout_stats.completed_workouts / workout_stats.total_workouts * 100) 
                if workout_stats.total_workouts > 0 else 0, 
                1
            ),
            'average_duration': round(workout_stats.avg_duration, 1) if workout_stats.avg_duration else None,
            'average_exertion': round(workout_stats.avg_exertion, 1) if workout_stats.avg_exertion else None
        }
    
    def _format_workout_response(self, workout_log: WorkoutLog, exercise_logs: List[ExerciseLog]) -> WorkoutLogResponse:
        """Format workout log and exercise logs into response schema"""
        
        exercises = [
            ExerciseLogResponse(
                id=ex_log.id,
                exercise_name=ex_log.exercise_name,
                exercise_id=ex_log.exercise_id,
                exercise_order=ex_log.exercise_order,
                planned_sets=ex_log.planned_sets,
                planned_reps=ex_log.planned_reps,
                planned_weight=ex_log.planned_weight,
                planned_rest_seconds=ex_log.planned_rest_seconds,
                actual_sets=ex_log.actual_sets or [],
                difficulty_rating=ex_log.difficulty_rating,
                exercise_notes=ex_log.exercise_notes,
                form_rating=ex_log.form_rating,
                created_at=ex_log.created_at
            )
            for ex_log in sorted(exercise_logs, key=lambda x: x.exercise_order)
        ]
        
        return WorkoutLogResponse(
            id=workout_log.id,
            assignment_id=workout_log.assignment_id,
            client_id=workout_log.client_id,
            workout_date=workout_log.workout_date,
            day_number=workout_log.day_number,
            workout_name=workout_log.workout_name,
            total_duration_minutes=workout_log.total_duration_minutes,
            perceived_exertion=workout_log.perceived_exertion,
            client_notes=workout_log.client_notes,
            trainer_feedback=workout_log.trainer_feedback,
            is_completed=workout_log.is_completed,
            is_skipped=workout_log.is_skipped,
            skip_reason=workout_log.skip_reason,
            exercises=exercises,
            created_at=workout_log.created_at
        )


# Global instance
workout_tracking_service = WorkoutTrackingService()