from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.utils.deps import get_current_trainer, get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.models.program_assignment import ProgramAssignment

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class WeekSummary(BaseModel):
    week_start: str        # "2026-03-30"
    week_label: str        # "Mar 30"
    total: int
    completed: int
    skipped: int
    pending: int
    completion_rate: float  # 0-100


class WorkoutStatsResponse(BaseModel):
    total_assigned: int
    total_completed: int
    total_skipped: int
    overall_rate: float
    current_streak: int
    longest_streak: int
    weekly_breakdown: List[WeekSummary]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _build_weekly_breakdown(exercises: list, num_weeks: int = 8) -> List[WeekSummary]:
    today = date.today()
    weeks = []
    for i in range(num_weeks - 1, -1, -1):
        week_start = _get_monday(today) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        week_exercises = [
            e for e in exercises
            if e.assigned_date and week_start <= e.assigned_date <= week_end
        ]
        total = len(week_exercises)
        completed = sum(1 for e in week_exercises if e.status == WeeklyExerciseStatus.COMPLETED)
        skipped = sum(1 for e in week_exercises if e.status == WeeklyExerciseStatus.SKIPPED)
        pending = total - completed - skipped
        weeks.append(WeekSummary(
            week_start=week_start.isoformat(),
            week_label=week_start.strftime("%b %d"),
            total=total,
            completed=completed,
            skipped=skipped,
            pending=pending,
            completion_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        ))
    return weeks


def _calc_streak(exercises: list) -> tuple[int, int]:
    """Return (current_streak_days, longest_streak_days) based on completed workout days."""
    completed_dates = sorted(set(
        e.assigned_date for e in exercises
        if e.status == WeeklyExerciseStatus.COMPLETED and e.assigned_date
    ))
    if not completed_dates:
        return 0, 0

    longest = current = 1
    prev = completed_dates[0]
    for d in completed_dates[1:]:
        if (d - prev).days == 1:
            current += 1
            longest = max(longest, current)
        elif (d - prev).days > 1:
            current = 1
        prev = d

    # current streak: count back from today
    today = date.today()
    streak = 0
    check = today
    date_set = set(completed_dates)
    while check in date_set:
        streak += 1
        check -= timedelta(days=1)

    return streak, longest


# ── Trainer endpoint: stats for a specific client ─────────────────────────────

@router.get("/clients/{client_id}/workout-stats", response_model=WorkoutStatsResponse)
def get_client_workout_stats(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    exercises = (
        db.query(WeeklyExerciseAssignment)
        .filter(
            and_(
                WeeklyExerciseAssignment.client_id == client_id,
                WeeklyExerciseAssignment.trainer_id == current_user.id,
            )
        )
        .all()
    )

    total = len(exercises)
    completed = sum(1 for e in exercises if e.status == WeeklyExerciseStatus.COMPLETED)
    skipped = sum(1 for e in exercises if e.status == WeeklyExerciseStatus.SKIPPED)
    streak, longest = _calc_streak(exercises)

    return WorkoutStatsResponse(
        total_assigned=total,
        total_completed=completed,
        total_skipped=skipped,
        overall_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        current_streak=streak,
        longest_streak=longest,
        weekly_breakdown=_build_weekly_breakdown(exercises),
    )


# ── Client self-view ──────────────────────────────────────────────────────────

@router.get("/my/workout-stats", response_model=WorkoutStatsResponse)
def get_my_workout_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return WorkoutStatsResponse(
            total_assigned=0, total_completed=0, total_skipped=0,
            overall_rate=0.0, current_streak=0, longest_streak=0,
            weekly_breakdown=_build_weekly_breakdown([]),
        )

    exercises = (
        db.query(WeeklyExerciseAssignment)
        .filter(WeeklyExerciseAssignment.client_id == client.id)
        .all()
    )

    total = len(exercises)
    completed = sum(1 for e in exercises if e.status == WeeklyExerciseStatus.COMPLETED)
    skipped = sum(1 for e in exercises if e.status == WeeklyExerciseStatus.SKIPPED)
    streak, longest = _calc_streak(exercises)

    return WorkoutStatsResponse(
        total_assigned=total,
        total_completed=completed,
        total_skipped=skipped,
        overall_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        current_streak=streak,
        longest_streak=longest,
        weekly_breakdown=_build_weekly_breakdown(exercises),
    )
