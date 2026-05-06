from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.user import User
from app.models.weekly_exercise import WeeklyExerciseAssignment, WeeklyExerciseStatus
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()


class WeekSummary(BaseModel):
    week_label: str
    week_start: str
    total: int
    completed: int
    skipped: int
    completion_rate: float


class CompletionStats(BaseModel):
    total_assigned: int
    total_completed: int
    total_skipped: int
    overall_rate: float
    current_streak: int
    weekly_breakdown: List[WeekSummary]


async def _streak(client_id: int, db: AsyncSession) -> int:
    stmt = (
        select(func.date(WeeklyExerciseAssignment.completed_date))
        .where(
            and_(
                WeeklyExerciseAssignment.client_id == client_id,
                WeeklyExerciseAssignment.status == WeeklyExerciseStatus.COMPLETED,
                WeeklyExerciseAssignment.completed_date.isnot(None),
            )
        )
        .distinct()
    )
    rows = (await db.execute(stmt)).all()
    days_with_completion = {row[0] for row in rows if row[0]}
    streak = 0
    check = date.today()
    while check in days_with_completion:
        streak += 1
        check -= timedelta(days=1)
    return streak


async def _weekly_breakdown(
    client_id: int, db: AsyncSession, weeks: int = 8
) -> List[WeekSummary]:
    result: List[WeekSummary] = []
    today = date.today()
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)

    for i in range(weeks):
        week_start = monday + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        stmt = select(WeeklyExerciseAssignment).where(
            and_(
                WeeklyExerciseAssignment.client_id == client_id,
                WeeklyExerciseAssignment.assigned_date >= week_start,
                WeeklyExerciseAssignment.assigned_date <= week_end,
            )
        )
        rows = list((await db.execute(stmt)).scalars().all())

        total = len(rows)
        completed = sum(1 for r in rows if r.status == WeeklyExerciseStatus.COMPLETED)
        skipped = sum(1 for r in rows if r.status == WeeklyExerciseStatus.SKIPPED)
        rate = round(completed / total * 100, 1) if total > 0 else 0.0

        result.append(
            WeekSummary(
                week_label=week_start.strftime("%b %d"),
                week_start=week_start.isoformat(),
                total=total,
                completed=completed,
                skipped=skipped,
                completion_rate=rate,
            )
        )
    return result


async def _summarise(
    client_id: int, db: AsyncSession, weeks: int
) -> CompletionStats:
    rows = list(
        (
            await db.execute(
                select(WeeklyExerciseAssignment).where(
                    WeeklyExerciseAssignment.client_id == client_id
                )
            )
        ).scalars().all()
    )
    total = len(rows)
    completed = sum(1 for r in rows if r.status == WeeklyExerciseStatus.COMPLETED)
    skipped = sum(1 for r in rows if r.status == WeeklyExerciseStatus.SKIPPED)

    return CompletionStats(
        total_assigned=total,
        total_completed=completed,
        total_skipped=skipped,
        overall_rate=round(completed / total * 100, 1) if total > 0 else 0.0,
        current_streak=await _streak(client_id, db),
        weekly_breakdown=await _weekly_breakdown(client_id, db, weeks),
    )


@router.get("/clients/{client_id}/completion", response_model=CompletionStats)
async def get_client_completion(
    client_id: int,
    weeks: int = 8,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Client).where(
        and_(Client.id == client_id, Client.trainer_id == current_user.id)
    )
    client = (await db.execute(stmt)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return await _summarise(client_id, db, weeks)


@router.get("/my/completion", response_model=CompletionStats)
async def get_my_completion(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return CompletionStats(
            total_assigned=0,
            total_completed=0,
            total_skipped=0,
            overall_rate=0.0,
            current_streak=0,
            weekly_breakdown=[],
        )
    return await _summarise(client.id, db, weeks)
