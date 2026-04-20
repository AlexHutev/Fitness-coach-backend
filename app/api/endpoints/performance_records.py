from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.utils.deps import get_current_trainer, get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.performance_record import PerformanceRecord

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


def verify_client(client_id: int, trainer_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# ── Trainer endpoints ─────────────────────────────────────────────────────────

@router.get("/clients/{client_id}/performance-records",
            response_model=List[PerformanceRecordResponse])
def get_performance_records(
    client_id: int,
    exercise_name: Optional[str] = None,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    query = db.query(PerformanceRecord).filter(
        PerformanceRecord.client_id == client_id
    )
    if exercise_name:
        query = query.filter(
            PerformanceRecord.exercise_name.ilike(f"%{exercise_name}%")
        )
    return query.order_by(
        PerformanceRecord.exercise_name,
        PerformanceRecord.recorded_at.asc()
    ).all()


@router.post("/clients/{client_id}/performance-records",
             response_model=PerformanceRecordResponse, status_code=201)
def create_performance_record(
    client_id: int,
    data: PerformanceRecordCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    record = PerformanceRecord(
        client_id=client_id,
        trainer_id=current_user.id,
        **data.dict()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/clients/{client_id}/performance-records/{record_id}",
            response_model=PerformanceRecordResponse)
def update_performance_record(
    client_id: int,
    record_id: int,
    data: PerformanceRecordUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    record = db.query(PerformanceRecord).filter(
        and_(PerformanceRecord.id == record_id,
             PerformanceRecord.client_id == client_id)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/clients/{client_id}/performance-records/{record_id}",
               status_code=204)
def delete_performance_record(
    client_id: int,
    record_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    record = db.query(PerformanceRecord).filter(
        and_(PerformanceRecord.id == record_id,
             PerformanceRecord.client_id == client_id)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()


# ── Client self-view ──────────────────────────────────────────────────────────

@router.get("/my/performance-records", response_model=List[PerformanceRecordResponse])
def get_my_performance_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return []
    return db.query(PerformanceRecord).filter(
        PerformanceRecord.client_id == client.id
    ).order_by(
        PerformanceRecord.exercise_name,
        PerformanceRecord.recorded_at.asc()
    ).all()
