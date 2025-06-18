from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models import (
    ProgramAssignment, WorkoutLog, ExerciseLog, Client, Program, Exercise
)
from app.schemas.client_schemas import (
    ClientDashboardResponse, ClientDashboardProgram, ClientProgressStats,
    WorkoutLogResponse, ExerciseLogResponse, ProgramTemplateForClient,
    WorkoutDayTemplate, WorkoutExerciseTemplate
)


class ClientDashboardService:
    
    def get_client_dashboard(self, db: Session, client_id: int) -> Optional[ClientDashboardResponse]:
        """Get complete dashboard data for a client"""
        
        # Get client info
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None
        
        # Get active programs
        active_programs = self._get_active_programs(db, client_id)
        
        # Get recent workouts (last 10)
        recent_workouts = self._get_recent_workouts(db, client_id, limit=10)
        
        # Get progress statistics
        progress_stats = self._get_progress_stats(db, client_id)
        
        return ClientDashboardResponse(
            client_id=client_id,
            client_name=f"{client.first_name} {client.last_name}",
            active_programs=active_programs,
            recent_workouts=recent_workouts,
            progress_stats=progress_stats
        )
    
    def _get_active_programs(self, db: Session, client_id: int) -> List[ClientDashboardProgram]:
        """Get all active program assignments for a client"""
        assignments = (
            db.query(ProgramAssignment)
            .join(Program)
            .filter(ProgramAssignment.client_id == client_id)
            .filter(ProgramAssignment.status == "active")
            .options(joinedload(ProgramAssignment.program))
            .all()
        )
        
        programs = []
        for assignment in assignments:
            program = assignment.program
            
            # Calculate completion percentage
            completion_percentage = 0
            if assignment.total_workouts > 0:
                completion_percentage = (assignment.completed_workouts / assignment.total_workouts) * 100
            
            # Determine next workout day
            next_workout_day = self._get_next_workout_day(db, assignment.id)
            
            programs.append(ClientDashboardProgram(
                assignment_id=assignment.id,
                program_id=program.id,
                program_name=program.name,
                program_description=program.description,
                program_type=program.program_type.value,
                difficulty_level=program.difficulty_level.value,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                status=assignment.status,
                total_workouts=assignment.total_workouts,
                completed_workouts=assignment.completed_workouts,
                completion_percentage=round(completion_percentage, 1),
                last_workout_date=assignment.last_workout_date,
                next_workout_day=next_workout_day
            ))
        
        return programs
    
    def _get_recent_workouts(self, db: Session, client_id: int, limit: int = 10) -> List[WorkoutLogResponse]:
        """Get recent workout logs for a client"""
        workout_logs = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.client_id == client_id)
            .order_by(desc(WorkoutLog.workout_date))
            .limit(limit)
            .options(joinedload(WorkoutLog.exercise_logs))
            .all()
        )
        
        workouts = []
        for log in workout_logs:
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
                for ex_log in sorted(log.exercise_logs, key=lambda x: x.exercise_order)
            ]
            
            workouts.append(WorkoutLogResponse(
                id=log.id,
                assignment_id=log.assignment_id,
                client_id=log.client_id,
                workout_date=log.workout_date,
                day_number=log.day_number,
                workout_name=log.workout_name,
                total_duration_minutes=log.total_duration_minutes,
                perceived_exertion=log.perceived_exertion,
                client_notes=log.client_notes,
                trainer_feedback=log.trainer_feedback,
                is_completed=log.is_completed,
                is_skipped=log.is_skipped,
                skip_reason=log.skip_reason,
                exercises=exercises,
                created_at=log.created_at
            ))
        
        return workouts
    
    def _get_progress_stats(self, db: Session, client_id: int) -> ClientProgressStats:
        """Calculate progress statistics for a client"""
        
        # Count programs
        total_programs = db.query(ProgramAssignment).filter(ProgramAssignment.client_id == client_id).count()
        active_programs = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client_id,
            ProgramAssignment.status == "active"
        ).count()
        completed_programs = db.query(ProgramAssignment).filter(
            ProgramAssignment.client_id == client_id,
            ProgramAssignment.status == "completed"
        ).count()
        
        # Count completed workouts
        total_workouts_completed = db.query(WorkoutLog).filter(
            WorkoutLog.client_id == client_id,
            WorkoutLog.is_completed == True
        ).count()
        
        # Calculate streaks
        current_streak = self._calculate_current_streak(db, client_id)
        longest_streak = self._calculate_longest_streak(db, client_id)
        
        # Calculate averages
        avg_duration = db.query(func.avg(WorkoutLog.total_duration_minutes)).filter(
            WorkoutLog.client_id == client_id,
            WorkoutLog.is_completed == True,
            WorkoutLog.total_duration_minutes.isnot(None)
        ).scalar()
        
        avg_exertion = db.query(func.avg(WorkoutLog.perceived_exertion)).filter(
            WorkoutLog.client_id == client_id,
            WorkoutLog.is_completed == True,
            WorkoutLog.perceived_exertion.isnot(None)
        ).scalar()
        
        return ClientProgressStats(
            total_programs=total_programs,
            active_programs=active_programs,
            completed_programs=completed_programs,
            total_workouts_completed=total_workouts_completed,
            current_streak=current_streak,
            longest_streak=longest_streak,
            average_workout_duration=round(avg_duration, 1) if avg_duration else None,
            average_perceived_exertion=round(avg_exertion, 1) if avg_exertion else None
        )
    
    def _get_next_workout_day(self, db: Session, assignment_id: int) -> Optional[int]:
        """Determine the next workout day for a program assignment"""
        # Get the latest workout for this assignment
        latest_workout = (
            db.query(WorkoutLog)
            .filter(WorkoutLog.assignment_id == assignment_id)
            .order_by(desc(WorkoutLog.day_number))
            .first()
        )
        
        if not latest_workout:
            return 1  # Start with day 1
        
        # Get the program to check total days
        assignment = db.query(ProgramAssignment).filter(ProgramAssignment.id == assignment_id).first()
        if not assignment or not assignment.program.workout_structure:
            return None
        
        total_days = len(assignment.program.workout_structure)
        
        # If completed workout was the last day, cycle back to day 1
        if latest_workout.day_number >= total_days:
            return 1
        
        return latest_workout.day_number + 1
    
    def _calculate_current_streak(self, db: Session, client_id: int) -> int:
        """Calculate current consecutive workout streak"""
        # Get workouts ordered by date descending
        workouts = (
            db.query(WorkoutLog.workout_date)
            .filter(WorkoutLog.client_id == client_id)
            .filter(WorkoutLog.is_completed == True)
            .order_by(desc(WorkoutLog.workout_date))
            .all()
        )
        
        if not workouts:
            return 0
        
        streak = 0
        current_date = datetime.now().date()
        
        for workout in workouts:
            workout_date = workout.workout_date.date()
            
            # Check if workout was today or yesterday (allowing for rest days)
            days_diff = (current_date - workout_date).days
            
            if days_diff <= 2:  # Allow up to 2 days gap for rest days
                streak += 1
                current_date = workout_date
            else:
                break
        
        return streak
    
    def _calculate_longest_streak(self, db: Session, client_id: int) -> int:
        """Calculate longest workout streak ever"""
        workouts = (
            db.query(WorkoutLog.workout_date)
            .filter(WorkoutLog.client_id == client_id)
            .filter(WorkoutLog.is_completed == True)
            .order_by(WorkoutLog.workout_date)
            .all()
        )
        
        if not workouts:
            return 0
        
        max_streak = 0
        current_streak = 1
        prev_date = workouts[0].workout_date.date()
        
        for i in range(1, len(workouts)):
            workout_date = workouts[i].workout_date.date()
            days_diff = (workout_date - prev_date).days
            
            if days_diff <= 2:  # Allow up to 2 days gap
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
            
            prev_date = workout_date
        
        return max(max_streak, current_streak)
    
    def get_program_template_for_client(self, db: Session, assignment_id: int) -> Optional[ProgramTemplateForClient]:
        """Get program template formatted for client viewing"""
        assignment = (
            db.query(ProgramAssignment)
            .options(joinedload(ProgramAssignment.program))
            .filter(ProgramAssignment.id == assignment_id)
            .first()
        )
        
        if not assignment or not assignment.program:
            return None
        
        program = assignment.program
        
        # Parse workout structure
        workout_days = []
        if program.workout_structure:
            for day_data in program.workout_structure:
                exercises = []
                
                for ex_data in day_data.get("exercises", []):
                    # Get exercise details if exercise_id is provided
                    exercise_details = None
                    if ex_data.get("exercise_id"):
                        exercise_details = db.query(Exercise).filter(
                            Exercise.id == ex_data["exercise_id"]
                        ).first()
                    
                    exercises.append(WorkoutExerciseTemplate(
                        exercise_id=ex_data.get("exercise_id"),
                        exercise_name=ex_data.get("name", "Unknown Exercise"),
                        sets=ex_data.get("sets", 1),
                        reps=ex_data.get("reps", "1"),
                        weight=ex_data.get("weight"),
                        rest_seconds=ex_data.get("rest_seconds", 60),
                        notes=ex_data.get("notes"),
                        muscle_groups=exercise_details.muscle_groups if exercise_details else [],
                        equipment=exercise_details.equipment if exercise_details else [],
                        instructions=exercise_details.instructions if exercise_details else None
                    ))
                
                workout_days.append(WorkoutDayTemplate(
                    day=day_data.get("day", 1),
                    name=day_data.get("name", f"Day {day_data.get('day', 1)}"),
                    exercises=exercises
                ))
        
        return ProgramTemplateForClient(
            program_id=program.id,
            assignment_id=assignment.id,
            program_name=program.name,
            program_description=program.description,
            program_type=program.program_type.value,
            difficulty_level=program.difficulty_level.value,
            duration_weeks=program.duration_weeks,
            sessions_per_week=program.sessions_per_week,
            workout_structure=workout_days,
            trainer_notes=assignment.assignment_notes
        )


# Global instance
client_dashboard_service = ClientDashboardService()