import json
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client import Client
from app.models.user import User
from app.models.weekly_exercise import (
    WeeklyExerciseAssignment,
    WeeklyExerciseStatus,
)
from app.schemas.weekly_exercise import (
    WeeklyExerciseResponse,
    WeeklyExerciseStatusUpdate,
    WeeklyExerciseWithDetails,
    WeeklySchedule,
)
from app.services.notification_service import NotificationService
from app.services.weekly_exercise_service import WeeklyExerciseService
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()


def _parse_muscle_groups(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return raw


def _enrich_exercise(exercise: WeeklyExerciseAssignment) -> WeeklyExerciseWithDetails:
    muscle_groups = (
        _parse_muscle_groups(exercise.exercise.muscle_groups)
        if exercise.exercise
        else []
    )
    program_name = (
        exercise.program_assignment.program.name
        if exercise.program_assignment and exercise.program_assignment.program
        else ""
    )
    payload = {
        **exercise.__dict__,
        "exercise_name": exercise.exercise.name if exercise.exercise else "Unknown Exercise",
        "exercise_description": exercise.exercise.description if exercise.exercise else "",
        "exercise_video_url": exercise.exercise.video_url if exercise.exercise else "",
        "exercise_instructions": exercise.exercise.instructions if exercise.exercise else "",
        "muscle_groups": muscle_groups,
        "program_name": program_name,
        "client_name": (
            f"{exercise.client.first_name} {exercise.client.last_name}"
            if exercise.client
            else ""
        ),
        "trainer_name": (
            f"{exercise.trainer.first_name} {exercise.trainer.last_name}"
            if exercise.trainer
            else ""
        ),
    }
    return WeeklyExerciseWithDetails(**payload)


@router.get(
    "/client/{client_id}/current-week",
    response_model=List[WeeklyExerciseWithDetails],
)
async def get_client_current_week_exercises(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercises = await WeeklyExerciseService.get_current_week_exercises(db, client_id)
    return [_enrich_exercise(ex) for ex in exercises]


@router.get(
    "/client/{client_id}/week", response_model=List[WeeklyExerciseWithDetails]
)
async def get_client_week_exercises(
    client_id: int,
    week_start: date = Query(...),
    status: Optional[WeeklyExerciseStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercises = await WeeklyExerciseService.get_client_weekly_exercises(
        db=db, client_id=client_id, week_start=week_start, status=status
    )
    return [_enrich_exercise(ex) for ex in exercises]


@router.put("/{exercise_id}/status", response_model=WeeklyExerciseResponse)
async def update_exercise_status(
    exercise_id: int,
    status_update: WeeklyExerciseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise_before = (
        await db.execute(
            select(WeeklyExerciseAssignment).where(
                WeeklyExerciseAssignment.id == exercise_id
            )
        )
    ).scalar_one_or_none()
    if not exercise_before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise assignment not found",
        )

    exercise = await WeeklyExerciseService.update_exercise_status(
        db=db,
        exercise_assignment_id=exercise_id,
        status=status_update.status,
        client_feedback=status_update.client_feedback,
        completion_percentage=status_update.completion_percentage,
    )
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise assignment not found",
        )

    client = (
        await db.execute(select(Client).where(Client.id == exercise.client_id))
    ).scalar_one_or_none()

    if (
        status_update.status == WeeklyExerciseStatus.SKIPPED
        and status_update.client_feedback
        and client
    ):
        # Reload exercise with eager 'exercise' relationship for the name
        ex_with_name = (
            await db.execute(
                select(WeeklyExerciseAssignment)
                .options(selectinload(WeeklyExerciseAssignment.exercise))
                .where(WeeklyExerciseAssignment.id == exercise_id)
            )
        ).scalar_one_or_none()
        exercise_name = (
            ex_with_name.exercise.name
            if ex_with_name and ex_with_name.exercise
            else "Unknown Exercise"
        )
        await NotificationService.create_exercise_not_completed_notification(
            db=db,
            trainer_id=exercise.trainer_id,
            client=client,
            exercise_name=exercise_name,
            reason=status_update.client_feedback,
        )

    if status_update.status == WeeklyExerciseStatus.COMPLETED and client:
        day_exercises_stmt = select(WeeklyExerciseAssignment).where(
            WeeklyExerciseAssignment.client_id == exercise.client_id,
            WeeklyExerciseAssignment.program_assignment_id
            == exercise.program_assignment_id,
            WeeklyExerciseAssignment.day_number == exercise.day_number,
            WeeklyExerciseAssignment.week_number == exercise.week_number,
        )
        day_exercises = list((await db.execute(day_exercises_stmt)).scalars().all())

        all_done = all(
            ex.status in (WeeklyExerciseStatus.COMPLETED, WeeklyExerciseStatus.SKIPPED)
            for ex in day_exercises
        )
        completed_count = sum(
            1 for ex in day_exercises if ex.status == WeeklyExerciseStatus.COMPLETED
        )

        if all_done and completed_count > 0:
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            day_name = (
                day_names[exercise.day_number - 1]
                if 1 <= exercise.day_number <= 7
                else f"Day {exercise.day_number}"
            )
            await NotificationService.create_day_completed_notification(
                db=db,
                trainer_id=exercise.trainer_id,
                client=client,
                day_name=day_name,
                exercises_completed=completed_count,
                total_exercises=len(day_exercises),
            )

    return exercise


@router.get("/client/{client_id}/schedule", response_model=WeeklySchedule)
async def get_client_weekly_schedule(
    client_id: int,
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    exercises = await WeeklyExerciseService.get_client_weekly_exercises(
        db=db, client_id=client_id, week_start=week_start
    )

    days: dict = {}
    total_exercises = len(exercises)
    completed_exercises = 0

    for exercise in exercises:
        day_key = f"day_{exercise.day_number}"
        days.setdefault(day_key, [])

        muscle_groups = (
            _parse_muscle_groups(exercise.exercise.muscle_groups)
            if exercise.exercise
            else []
        )
        days[day_key].append(
            {
                "id": exercise.id,
                "exercise_id": exercise.exercise_id,
                "exercise_name": exercise.exercise.name
                if exercise.exercise
                else "Unknown Exercise",
                "exercise_description": exercise.exercise.description
                if exercise.exercise
                else "",
                "exercise_video_url": exercise.exercise.video_url
                if exercise.exercise
                else "",
                "exercise_instructions": exercise.exercise.instructions
                if exercise.exercise
                else "",
                "sets": exercise.sets,
                "reps": exercise.reps,
                "weight": exercise.weight,
                "rest_seconds": exercise.rest_seconds,
                "exercise_notes": exercise.exercise_notes,
                "status": exercise.status.value,
                "completion_percentage": exercise.completion_percentage,
                "due_date": exercise.due_date,
                "exercise_order": exercise.exercise_order,
                "day_number": exercise.day_number,
                "client_feedback": exercise.client_feedback,
                "trainer_feedback": exercise.trainer_feedback,
                "muscle_groups": muscle_groups,
            }
        )

        if exercise.status == WeeklyExerciseStatus.COMPLETED:
            completed_exercises += 1

    for day in days.values():
        day.sort(key=lambda x: x["exercise_order"])

    completion_percentage = (
        int(completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
    )

    return WeeklySchedule(
        week_start=week_start,
        week_end=week_end,
        total_exercises=total_exercises,
        completed_exercises=completed_exercises,
        completion_percentage=completion_percentage,
        days=days,
    )


@router.get("/trainer/clients-summary", response_model=List[dict])
async def get_trainer_clients_weekly_summary(
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
):
    return [{"message": "Feature coming soon"}]
