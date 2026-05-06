from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.goal_milestone import GoalMilestone
from app.models.user import User
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()

GOAL_TYPES = [
    "weight_loss",
    "weight_gain",
    "muscle_gain",
    "endurance",
    "strength",
    "general_fitness",
    "rehabilitation",
    "custom",
]
METRICS = [
    "weight",
    "body_fat_percentage",
    "muscle_mass",
    "waist",
    "chest",
    "arms",
    "thighs",
    "custom",
]


class GoalCreate(BaseModel):
    title: str
    goal_type: str
    metric: str
    unit: str
    start_value: float
    target_value: float
    current_value: Optional[float] = None
    start_date: date
    target_date: Optional[date] = None
    notes: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    goal_type: Optional[str] = None
    metric: Optional[str] = None
    unit: Optional[str] = None
    start_value: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    is_completed: Optional[bool] = None
    completed_date: Optional[date] = None
    notes: Optional[str] = None


class GoalResponse(BaseModel):
    id: int
    client_id: int
    trainer_id: int
    title: str
    goal_type: str
    metric: str
    unit: Optional[str]
    start_value: float
    target_value: float
    current_value: Optional[float]
    start_date: date
    target_date: Optional[date]
    is_completed: bool
    completed_date: Optional[date]
    notes: Optional[str]
    progress_pct: float = 0.0

    class Config:
        from_attributes = True


def _compute_progress(goal: GoalMilestone) -> float:
    if goal.current_value is None:
        return 0.0
    total = abs(goal.target_value - goal.start_value)
    if total == 0:
        return 100.0 if goal.is_completed else 0.0
    done = abs(goal.current_value - goal.start_value)
    return round(min(done / total * 100, 100), 1)


def _to_response(goal: GoalMilestone) -> GoalResponse:
    data = GoalResponse.model_validate(goal)
    data.progress_pct = _compute_progress(goal)
    return data


async def _verify_client(
    client_id: int, trainer_id: int, db: AsyncSession
) -> Client:
    stmt = select(Client).where(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    )
    client = (await db.execute(stmt)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/clients/{client_id}/goals", response_model=List[GoalResponse])
async def get_goals(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = (
        select(GoalMilestone)
        .where(GoalMilestone.client_id == client_id)
        .order_by(GoalMilestone.created_at.desc())
    )
    goals = list((await db.execute(stmt)).scalars().all())
    return [_to_response(g) for g in goals]


@router.post(
    "/clients/{client_id}/goals", response_model=GoalResponse, status_code=201
)
async def create_goal(
    client_id: int,
    data: GoalCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    goal = GoalMilestone(
        client_id=client_id, trainer_id=current_user.id, **data.dict()
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return _to_response(goal)


@router.put(
    "/clients/{client_id}/goals/{goal_id}", response_model=GoalResponse
)
async def update_goal(
    client_id: int,
    goal_id: int,
    data: GoalUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(GoalMilestone).where(
        and_(GoalMilestone.id == goal_id, GoalMilestone.client_id == client_id)
    )
    goal = (await db.execute(stmt)).scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(goal, field, value)
    await db.commit()
    await db.refresh(goal)
    return _to_response(goal)


@router.delete("/clients/{client_id}/goals/{goal_id}", status_code=204)
async def delete_goal(
    client_id: int,
    goal_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(GoalMilestone).where(
        and_(GoalMilestone.id == goal_id, GoalMilestone.client_id == client_id)
    )
    goal = (await db.execute(stmt)).scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)
    await db.commit()


@router.get("/my/goals", response_model=List[GoalResponse])
async def get_my_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return []
    stmt = (
        select(GoalMilestone)
        .where(GoalMilestone.client_id == client.id)
        .order_by(GoalMilestone.created_at.desc())
    )
    goals = list((await db.execute(stmt)).scalars().all())
    return [_to_response(g) for g in goals]
