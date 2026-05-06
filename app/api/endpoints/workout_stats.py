from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.user import User
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()


class WeekSummary(BaseModel):
    week_start: str
    week_label: str
    total: int
    completed: int
    skipped: int
    pending: int
    completion_rate: float


class WorkoutStatsResponse(BaseModel):
    total_assigned: int
    total_completed: int
    total_skipped: int
    overall_rate: float
    current_streak: int
    longest_streak: int
    weekly_breakdown: List[WeekSummary]


def _get_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _build_weekly_breakdown(exercises: list, num_weeks: int = 8) -> List[WeekSummary]:
    today = date.today()
    weeks: List[WeekSummary] = []
    for i in range(num_weeks - 1, -1, -1):
        week_start = _get_monday(today) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        week_exercises = [
            e
            for e in exercises
            if e.assigned_date and week_start <= e.assigned_date <= week_end
        ]
        total = len(week_exercises)
        completed = sum(
            1 for e in week_exercises if e.status == WeeklyExerciseStatus.COMPLETED
        )
        skipped = sum(
            1 for e in week_exercises if e.status == WeeklyExerciseStatus.SKIPPED
        )
        pending = total - completed - skipped
        weeks.append(
            WeekSummary(
                week_start=week_start.isoformat(),
                week_label=week_start.strftime("%b %d"),
                total=total,
                completed=completed,
                skipped=skipped,
                pending=pending,
                completion_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
            )
        )
    return weeks


def _calc_streak(exercises: list) -> tuple[int, int]:
    completed_dates = sorted(
        {
            e.assigned_date
            for e in exercises
            if e.status == WeeklyExerciseStatus.COMPLETED and e.assigned_date
        }
    )
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

    today = date.today()
    streak = 0
    check = today
    date_set = set(completed_dates)
    while check in date_set:
        streak += 1
        check -= timedelta(days=1)
    return streak, longest


def _stats(exercises: list) -> WorkoutStatsResponse:
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


@router.get(
    "/clients/{client_id}/workout-stats", response_model=WorkoutStatsResponse
)
async def get_client_workout_stats(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WeeklyExerciseAssignment).where(
        and_(
            WeeklyExerciseAssignment.client_id == client_id,
            WeeklyExerciseAssignment.trainer_id == current_user.id,
        )
    )
    exercises = list((await db.execute(stmt)).scalars().all())
    return _stats(exercises)


@router.get("/my/workout-stats", response_model=WorkoutStatsResponse)
async def get_my_workout_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return _stats([])

    stmt = select(WeeklyExerciseAssignment).where(
        WeeklyExerciseAssignment.client_id == client.id
    )
    exercises = list((await db.execute(stmt)).scalars().all())
    return _stats(exercises)
