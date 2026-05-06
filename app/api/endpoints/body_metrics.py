from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.body_metric import BodyMetric
from app.models.client import Client
from app.models.user import User
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class BodyMetricCreate(BaseModel):
    measured_at: date
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    waist: Optional[float] = None
    chest: Optional[float] = None
    hips: Optional[float] = None
    arms: Optional[float] = None
    thighs: Optional[float] = None
    notes: Optional[str] = None


class BodyMetricUpdate(BaseModel):
    measured_at: Optional[date] = None
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    waist: Optional[float] = None
    chest: Optional[float] = None
    hips: Optional[float] = None
    arms: Optional[float] = None
    thighs: Optional[float] = None
    notes: Optional[str] = None


class BodyMetricResponse(BaseModel):
    id: int
    client_id: int
    measured_at: date
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    waist: Optional[float] = None
    chest: Optional[float] = None
    hips: Optional[float] = None
    arms: Optional[float] = None
    thighs: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _verify_client(client_id: int, trainer_id: int, db: AsyncSession) -> Client:
    stmt = select(Client).where(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    )
    client = (await db.execute(stmt)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# ── Trainer endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/clients/{client_id}/body-metrics", response_model=List[BodyMetricResponse]
)
async def get_body_metrics(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = (
        select(BodyMetric)
        .where(BodyMetric.client_id == client_id)
        .order_by(BodyMetric.measured_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post(
    "/clients/{client_id}/body-metrics",
    response_model=BodyMetricResponse,
    status_code=201,
)
async def create_body_metric(
    client_id: int,
    data: BodyMetricCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    metric = BodyMetric(client_id=client_id, **data.dict())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.put(
    "/clients/{client_id}/body-metrics/{metric_id}", response_model=BodyMetricResponse
)
async def update_body_metric(
    client_id: int,
    metric_id: int,
    data: BodyMetricUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(BodyMetric).where(
        and_(BodyMetric.id == metric_id, BodyMetric.client_id == client_id)
    )
    metric = (await db.execute(stmt)).scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(metric, field, value)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.delete(
    "/clients/{client_id}/body-metrics/{metric_id}", status_code=204
)
async def delete_body_metric(
    client_id: int,
    metric_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(BodyMetric).where(
        and_(BodyMetric.id == metric_id, BodyMetric.client_id == client_id)
    )
    metric = (await db.execute(stmt)).scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    await db.delete(metric)
    await db.commit()


# ── Client self-view ──────────────────────────────────────────────────────────

@router.get("/my/body-metrics", response_model=List[BodyMetricResponse])
async def get_my_body_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client can view their own body metric history."""
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return []
    stmt = (
        select(BodyMetric)
        .where(BodyMetric.client_id == client.id)
        .order_by(BodyMetric.measured_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())
