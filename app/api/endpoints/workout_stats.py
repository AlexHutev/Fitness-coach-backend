from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.utils.deps import get_current_trainer, get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.models.workout_tracking import WorkoutLog
from app.models.program_assignment import ProgramAssignment

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────

class WeeklyStats(BaseModel):
    week_label: str        # e.g. "Mar 31"
    week_start: str        # ISO date
    completed: int
    skipped: int
    pending: int
    total: int
    completion_rate: float  # 0-100


class WorkoutSummary(BaseModel):
    total_assigned: int
    total_completed: int
    total_skipped: int
    total_pending: int
    overall_completion_rate: float
    current_streak_days: int
    longest_streak_days: int
    last_workout_date: Optional[str]
    weekly_stats: List[WeeklyStats]


def compute_stats(db: Session, client_id: int, weeks: int = 12) -> WorkoutSummary:
    """Build workout completion stats for a given client."""

    # ── Overall counts ────────────────────────────────────────────────────────
    all_rows = (
        db.query(WeeklyExerciseAssignment)
        .filter(WeeklyExerciseAssignment.client_id == client_id)
        .all()
    )
    total_assigned = len(all_rows)
    total_completed = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.COMPLETED)
    total_skipped   = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.SKIPPED)
    total_pending   = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.PENDING)
    overall_rate    = round(total_completed / total_assigned * 100, 1) if total_assigned else 0.0

    # ── Last workout date ─────────────────────────────────────────────────────
    last = (
        db.query(WeeklyExerciseAssignment)
        .filter(
            and_(
                WeeklyExerciseAssignment.client_id == client_id,
                WeeklyExerciseAssignment.status == WeeklyExerciseStatus.COMPLETED,
            )
        )
        .order_by(WeeklyExerciseAssignment.completed_date.desc())
        .first()
    )
    last_date = last.completed_date.date() if last and last.completed_date else None

    # ── Streak calculation ────────────────────────────────────────────────────
    completed_dates = sorted({
        r.completed_date.date()
        for r in all_rows
        if r.status == WeeklyExerciseStatus.COMPLETED and r.completed_date
    })

    current_streak = 0
    longest_streak = 0
    if completed_dates:
        # Current streak: count backwards from today
        check = date.today()
        for d in reversed(completed_dates):
            if d == check or d == check - timedelta(days=1):
                current_streak += 1
                check = d - timedelta(days=1)
            elif d < check:
                break
        # Longest streak: sliding window
        streak = 1
        for i in range(1, len(completed_dates)):
            if (completed_dates[i] - completed_dates[i-1]).days == 1:
                streak += 1
                longest_streak = max(longest_streak, streak)
            else:
                streak = 1
        longest_streak = max(longest_streak, streak)

    # ── Weekly breakdown ──────────────────────────────────────────────────────
    today = date.today()
    monday = today - timedelta(days=today.weekday())  # start of current week

    weekly_stats: List[WeeklyStats] = []
    for i in range(weeks - 1, -1, -1):
        week_start = monday - timedelta(weeks=i)
        week_end   = week_start + timedelta(days=6)

        rows = [
            r for r in all_rows
            if r.assigned_date and week_start <= r.assigned_date <= week_end
        ]
        wc = sum(1 for r in rows if r.status == WeeklyExerciseStatus.COMPLETED)
        ws = sum(1 for r in rows if r.status == WeeklyExerciseStatus.SKIPPED)
        wp = sum(1 for r in rows if r.status == WeeklyExerciseStatus.PENDING)
        wt = len(rows)
        wr = round(wc / wt * 100, 1) if wt else 0.0

        weekly_stats.append(WeeklyStats(
            week_label=week_start.strftime("%b %-d") if hasattr(week_start, 'strftime') else week_start.strftime("%b %d").lstrip("0"),
            week_start=week_start.isoformat(),
            completed=wc, skipped=ws, pending=wp,
            total=wt, completion_rate=wr,
        ))

    return WorkoutSummary(
        total_assigned=total_assigned,
        total_completed=total_completed,
        total_skipped=total_skipped,
        total_pending=total_pending,
        overall_completion_rate=overall_rate,
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
        last_workout_date=last_date.isoformat() if last_date else None,
        weekly_stats=weekly_stats,
    )

