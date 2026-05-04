"""Trainer dashboard summary endpoint.

Returns the four headline stats shown on the trainer's home dashboard
in a single round-trip:
  - active clients (with this-month delta)
  - programs created (with this-week delta)
  - sessions this week (with remaining count)
  - average client progress across active program assignments
"""
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.client import Client
from app.models.program import Program
from app.models.program_assignment import AssignmentStatus, ProgramAssignment
from app.models.schedule import Appointment
from app.models.user import User
from app.schemas.dashboard import (
    ActiveClientsStat,
    ClientProgressStat,
    ProgramsStat,
    SessionsStat,
    TrainerDashboardStats,
)
from app.utils.deps import get_current_trainer

router = APIRouter()


def _start_of_week(now: datetime) -> datetime:
    """Monday 00:00 of the week containing `now` (timezone-naive UTC)."""
    monday = now.date() - timedelta(days=now.weekday())
    return datetime.combine(monday, time.min)


def _end_of_week(now: datetime) -> datetime:
    """Sunday 23:59:59.999999 of the week containing `now`."""
    sunday = now.date() + timedelta(days=(6 - now.weekday()))
    return datetime.combine(sunday, time.max)


def _start_of_month(now: datetime) -> datetime:
    return datetime.combine(now.date().replace(day=1), time.min)


@router.get("/trainer-stats", response_model=TrainerDashboardStats)
def get_trainer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_trainer),
) -> TrainerDashboardStats:
    """Aggregate the four headline stats for the trainer's dashboard."""
    # Use naive UTC "now" because most timestamp columns are stored as
    # naive UTC via server_default=func.now().
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    week_start = _start_of_week(now)
    week_end = _end_of_week(now)
    month_start = _start_of_month(now)

    trainer_id = current_user.id

    # ── Active clients ────────────────────────────────────────────────
    active_clients_total = (
        db.query(func.count(Client.id))
        .filter(Client.trainer_id == trainer_id, Client.is_active.is_(True))
        .scalar()
        or 0
    )
    active_clients_delta = (
        db.query(func.count(Client.id))
        .filter(
            Client.trainer_id == trainer_id,
            Client.is_active.is_(True),
            Client.created_at >= month_start,
        )
        .scalar()
        or 0
    )

    # ── Programs ──────────────────────────────────────────────────────
    programs_total = (
        db.query(func.count(Program.id))
        .filter(Program.trainer_id == trainer_id, Program.is_active.is_(True))
        .scalar()
        or 0
    )
    programs_delta = (
        db.query(func.count(Program.id))
        .filter(
            Program.trainer_id == trainer_id,
            Program.is_active.is_(True),
            Program.created_at >= week_start,
        )
        .scalar()
        or 0
    )

    # ── Sessions this week ────────────────────────────────────────────
    sessions_total = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.trainer_id == trainer_id,
            Appointment.start_time >= week_start,
            Appointment.start_time <= week_end,
        )
        .scalar()
        or 0
    )
    sessions_remaining = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.trainer_id == trainer_id,
            Appointment.start_time >= now,
            Appointment.start_time <= week_end,
            Appointment.status.in_(("scheduled", "confirmed", "pending")),
        )
        .scalar()
        or 0
    )

    # ── Client progress (avg of completion_percentage over active assignments) ──
    avg_progress_raw = (
        db.query(func.avg(ProgramAssignment.completion_percentage))
        .filter(
            ProgramAssignment.trainer_id == trainer_id,
            ProgramAssignment.status == AssignmentStatus.ACTIVE,
        )
        .scalar()
    )
    avg_progress = int(round(avg_progress_raw)) if avg_progress_raw is not None else 0

    return TrainerDashboardStats(
        active_clients=ActiveClientsStat(
            total=active_clients_total,
            delta_this_month=active_clients_delta,
        ),
        programs=ProgramsStat(
            total=programs_total,
            delta_this_week=programs_delta,
        ),
        sessions_this_week=SessionsStat(
            total=sessions_total,
            remaining=sessions_remaining,
        ),
        client_progress=ClientProgressStat(
            average_percentage=avg_progress,
        ),
    )
