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
from app.models.body_metric import BodyMetric

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

def verify_client(client_id: int, trainer_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.trainer_id == trainer_id)
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# ── Trainer endpoints ─────────────────────────────────────────────────────────

@router.get("/clients/{client_id}/body-metrics", response_model=List[BodyMetricResponse])
def get_body_metrics(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.client_id == client_id)
        .order_by(BodyMetric.measured_at.asc())
        .all()
    )


@router.post("/clients/{client_id}/body-metrics", response_model=BodyMetricResponse, status_code=201)
def create_body_metric(
    client_id: int,
    data: BodyMetricCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    metric = BodyMetric(client_id=client_id, **data.dict())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.put("/clients/{client_id}/body-metrics/{metric_id}", response_model=BodyMetricResponse)
def update_body_metric(
    client_id: int,
    metric_id: int,
    data: BodyMetricUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    metric = db.query(BodyMetric).filter(
        and_(BodyMetric.id == metric_id, BodyMetric.client_id == client_id)
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(metric, field, value)
    db.commit()
    db.refresh(metric)
    return metric


@router.delete("/clients/{client_id}/body-metrics/{metric_id}", status_code=204)
def delete_body_metric(
    client_id: int,
    metric_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db),
):
    verify_client(client_id, current_user.id, db)
    metric = db.query(BodyMetric).filter(
        and_(BodyMetric.id == metric_id, BodyMetric.client_id == client_id)
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    db.delete(metric)
    db.commit()


# ── Client self-view ──────────────────────────────────────────────────────────

@router.get("/my/body-metrics", response_model=List[BodyMetricResponse])
def get_my_body_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client can view their own body metric history."""
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return []
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.client_id == client.id)
        .order_by(BodyMetric.measured_at.asc())
        .all()
    )
