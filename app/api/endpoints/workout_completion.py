from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Integer
from datetime import date, timedelta
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.utils.deps import get_current_trainer, get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.models.workout_tracking import WorkoutLog

router = APIRouter()


class WeekSummary(BaseModel):
    week_label: str       # e.g. "Mar 31"
    week_start: str       # ISO date
    total: int
    completed: int
    skipped: int
    completion_rate: float


class CompletionStats(BaseModel):
    total_assigned: int
    total_completed: int
    total_skipped: int
    overall_rate: float
    current_streak: int   # consecutive days with at least one completion
    weekly_breakdown: List[WeekSummary]


def _streak(client_id: int, db: Session) -> int:
    """Count consecutive days (backwards from today) that had at least one completion."""
    completed = (
        db.query(func.date(WeeklyExerciseAssignment.completed_date))
        .filter(
            and_(
                WeeklyExerciseAssignment.client_id == client_id,
                WeeklyExerciseAssignment.status == WeeklyExerciseStatus.COMPLETED,
                WeeklyExerciseAssignment.completed_date.isnot(None),
            )
        )
        .distinct()
        .all()
    )
    days_with_completion = {row[0] for row in completed if row[0]}
    streak = 0
    check = date.today()
    while check in days_with_completion:
        streak += 1
        check -= timedelta(days=1)
    return streak


def _weekly_breakdown(client_id: int, db: Session, weeks: int = 8) -> List[WeekSummary]:
    result = []
    today = date.today()
    # Start from the Monday of (weeks) ago
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)

    for i in range(weeks):
        week_start = monday + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        rows = (
            db.query(WeeklyExerciseAssignment)
            .filter(
                and_(
                    WeeklyExerciseAssignment.client_id == client_id,
                    WeeklyExerciseAssignment.assigned_date >= week_start,
                    WeeklyExerciseAssignment.assigned_date <= week_end,
                )
            )
            .all()
        )

        total = len(rows)
        completed = sum(1 for r in rows if r.status == WeeklyExerciseStatus.COMPLETED)
        skipped = sum(1 for r in rows if r.status == WeeklyExerciseStatus.SKIPPED)
        rate = round(completed / total * 100, 1) if total > 0 else 0.0

        result.append(WeekSummary(
            week_label=week_start.strftime("%b %d"),
            week_start=week_start.isoformat(),
            total=total,
            completed=completed,
            skipped=skipped,
            completion_rate=rate,
        ))
    return result


# ── Trainer: get completion stats for a specific client ───────────────────────

@router.get("/clients/{client_id}/completion", response_model=CompletionStats)
def get_client_completion(
    client_id: int,
    weeks: int = 8,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.trainer_id == current_user.id)
    ).first()
    if not client:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Client not found")

    all_rows = db.query(WeeklyExerciseAssignment).filter(
        WeeklyExerciseAssignment.client_id == client_id
    ).all()

    total = len(all_rows)
    completed = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.COMPLETED)
    skipped = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.SKIPPED)

    return CompletionStats(
        total_assigned=total,
        total_completed=completed,
        total_skipped=skipped,
        overall_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        current_streak=_streak(client_id, db),
        weekly_breakdown=_weekly_breakdown(client_id, db, weeks),
    )


# ── Client self-view ──────────────────────────────────────────────────────────

@router.get("/my/completion", response_model=CompletionStats)
def get_my_completion(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return CompletionStats(
            total_assigned=0, total_completed=0, total_skipped=0,
            overall_rate=0.0, current_streak=0, weekly_breakdown=[],
        )

    all_rows = db.query(WeeklyExerciseAssignment).filter(
        WeeklyExerciseAssignment.client_id == client.id
    ).all()

    total = len(all_rows)
    completed = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.COMPLETED)
    skipped = sum(1 for r in all_rows if r.status == WeeklyExerciseStatus.SKIPPED)

    return CompletionStats(
        total_assigned=total,
        total_completed=completed,
        total_skipped=skipped,
        overall_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        current_streak=_streak(client.id, db),
        weekly_breakdown=_weekly_breakdown(client.id, db, weeks),
    )
