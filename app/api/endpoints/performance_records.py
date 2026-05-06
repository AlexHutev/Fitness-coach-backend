from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.client import Client
from app.models.performance_record import PerformanceRecord
from app.models.user import User
from app.utils.deps import get_current_trainer, get_current_user

router = APIRouter()

RECORD_TYPES = ["1RM", "Max Reps", "Best Time", "Max Distance", "Best Pace"]
UNITS = ["kg", "lbs", "reps", "seconds", "minutes", "km", "miles"]


class PerformanceRecordCreate(BaseModel):
    exercise_name: str
    value: float
    unit: str
    record_type: str
    recorded_at: date
    notes: Optional[str] = None


class PerformanceRecordUpdate(BaseModel):
    exercise_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    record_type: Optional[str] = None
    recorded_at: Optional[date] = None
    notes: Optional[str] = None


class PerformanceRecordResponse(BaseModel):
    id: int
    client_id: int
    trainer_id: int
    exercise_name: str
    value: float
    unit: str
    record_type: str
    recorded_at: date
    notes: Optional[str] = None
    is_pr: int

    class Config:
        from_attributes = True


async def _verify_client(client_id: int, trainer_id: int, db: AsyncSession) -> Client:
    stmt = select(Client).where(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    )
    client = (await db.execute(stmt)).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get(
    "/clients/{client_id}/performance-records",
    response_model=List[PerformanceRecordResponse],
)
async def get_performance_records(
    client_id: int,
    exercise_name: Optional[str] = None,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(PerformanceRecord).where(PerformanceRecord.client_id == client_id)
    if exercise_name:
        stmt = stmt.where(PerformanceRecord.exercise_name.ilike(f"%{exercise_name}%"))
    stmt = stmt.order_by(
        PerformanceRecord.exercise_name, PerformanceRecord.recorded_at.asc()
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post(
    "/clients/{client_id}/performance-records",
    response_model=PerformanceRecordResponse,
    status_code=201,
)
async def create_performance_record(
    client_id: int,
    data: PerformanceRecordCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    record = PerformanceRecord(
        client_id=client_id, trainer_id=current_user.id, **data.dict()
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.put(
    "/clients/{client_id}/performance-records/{record_id}",
    response_model=PerformanceRecordResponse,
)
async def update_performance_record(
    client_id: int,
    record_id: int,
    data: PerformanceRecordUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(PerformanceRecord).where(
        and_(
            PerformanceRecord.id == record_id,
            PerformanceRecord.client_id == client_id,
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete(
    "/clients/{client_id}/performance-records/{record_id}", status_code=204
)
async def delete_performance_record(
    client_id: int,
    record_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    await _verify_client(client_id, current_user.id, db)
    stmt = select(PerformanceRecord).where(
        and_(
            PerformanceRecord.id == record_id,
            PerformanceRecord.client_id == client_id,
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(record)
    await db.commit()


@router.get("/my/performance-records", response_model=List[PerformanceRecordResponse])
async def get_my_performance_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = (
        await db.execute(select(Client).where(Client.user_id == current_user.id))
    ).scalar_one_or_none()
    if not client:
        return []
    stmt = (
        select(PerformanceRecord)
        .where(PerformanceRecord.client_id == client.id)
        .order_by(
            PerformanceRecord.exercise_name, PerformanceRecord.recorded_at.asc()
        )
    )
    return list((await db.execute(stmt)).scalars().all())
