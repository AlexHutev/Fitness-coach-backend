from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client import Client
from app.models.program_assignment import AssignmentStatus, ProgramAssignment
from app.models.schedule import Appointment
from app.models.user import User, UserRole
from app.models.workout_tracking import WorkoutLog
from app.services.client_account_service import ClientAccountService
from app.utils.deps import get_current_user

router = APIRouter()


async def get_current_client(current_user: User = Depends(get_current_user)) -> User:
    """Restrict to users with the CLIENT role."""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Client role required.",
        )
    return current_user


def _calculate_profile_completion(client_record: Client) -> int:
    total_fields = 9
    completed = 0
    if client_record.height:
        completed += 1
    if client_record.weight:
        completed += 1
    if client_record.body_fat_percentage:
        completed += 1
    if client_record.activity_level:
        completed += 1
    if client_record.primary_goal:
        completed += 1
    if client_record.date_of_birth:
        completed += 1
    if client_record.gender:
        completed += 1
    if client_record.emergency_contact_name:
        completed += 1
    if client_record.emergency_contact_phone:
        completed += 1
    return round((completed / total_fields) * 100)


def _missing_profile_fields(client_record: Client) -> list:
    missing = []
    if not client_record.height:
        missing.append("height")
    if not client_record.weight:
        missing.append("weight")
    if not client_record.activity_level:
        missing.append("activity_level")
    if not client_record.primary_goal:
        missing.append("primary_goal")
    if not client_record.date_of_birth:
        missing.append("date_of_birth")
    if not client_record.gender:
        missing.append("gender")
    if not client_record.emergency_contact_name:
        missing.append("emergency_contact_name")
    if not client_record.emergency_contact_phone:
        missing.append("emergency_contact_phone")
    return missing


async def _client_with_trainer(db: AsyncSession, user_id: int) -> Client | None:
    stmt = (
        select(Client)
        .options(selectinload(Client.trainer))
        .where(Client.user_id == user_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


@router.get("/profile")
async def get_client_profile(
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    client_record = await _client_with_trainer(db, current_user.id)
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
        )

    return {
        "user_info": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number,
        },
        "client_info": {
            "id": client_record.id,
            "height": client_record.height,
            "weight": client_record.weight,
            "body_fat_percentage": client_record.body_fat_percentage,
            "activity_level": client_record.activity_level,
            "primary_goal": client_record.primary_goal,
            "secondary_goals": client_record.secondary_goals,
            "medical_conditions": client_record.medical_conditions,
            "injuries": client_record.injuries,
            "date_of_birth": client_record.date_of_birth,
            "gender": client_record.gender,
        },
        "trainer_info": {
            "id": client_record.trainer.id,
            "name": f"{client_record.trainer.first_name} {client_record.trainer.last_name}",
            "email": client_record.trainer.email,
            "specialization": client_record.trainer.specialization,
        },
    }


@router.get("/programs")
async def get_client_programs(
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    client_record = await ClientAccountService.get_client_by_user_id(db, current_user.id)
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
        )

    stmt = (
        select(ProgramAssignment)
        .options(
            selectinload(ProgramAssignment.program),
            selectinload(ProgramAssignment.trainer),
        )
        .where(
            ProgramAssignment.client_id == client_record.id,
            ProgramAssignment.status == AssignmentStatus.ACTIVE,
        )
    )
    assignments = list((await db.execute(stmt)).scalars().all())

    assigned_programs = []
    for assignment in assignments:
        assigned_programs.append(
            {
                "assignment_id": assignment.id,
                "program_id": assignment.program_id,
                "program_name": assignment.program.name,
                "program_description": assignment.program.description,
                "program_type": assignment.program.program_type,
                "difficulty_level": assignment.program.difficulty_level,
                "duration_weeks": assignment.program.duration_weeks,
                "workout_structure": assignment.program.workout_structure,
                "assigned_date": (
                    assignment.assigned_date.isoformat()
                    if assignment.assigned_date
                    else None
                ),
                "start_date": (
                    assignment.start_date.isoformat() if assignment.start_date else None
                ),
                "end_date": (
                    assignment.end_date.isoformat() if assignment.end_date else None
                ),
                "status": assignment.status.value,
                "completion_percentage": assignment.completion_percentage,
                "sessions_completed": assignment.sessions_completed,
                "total_sessions": assignment.total_sessions,
                "custom_notes": assignment.custom_notes,
                "trainer_notes": assignment.trainer_notes,
                "trainer_info": {
                    "id": assignment.trainer.id,
                    "name": f"{assignment.trainer.first_name} {assignment.trainer.last_name}",
                    "email": assignment.trainer.email,
                    "specialization": assignment.trainer.specialization,
                },
            }
        )

    return {
        "assigned_programs": assigned_programs,
        "total_assignments": len(assigned_programs),
    }


@router.get("/dashboard-stats")
async def get_client_dashboard_stats(
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    client_record = await ClientAccountService.get_client_by_user_id(db, current_user.id)
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
        )

    bmi = None
    if client_record.height and client_record.weight:
        height_m = client_record.height / 100
        bmi = round(client_record.weight / (height_m**2), 1)

    active_programs = int(
        (
            await db.execute(
                select(func.count(ProgramAssignment.id)).where(
                    ProgramAssignment.client_id == client_record.id,
                    ProgramAssignment.status == AssignmentStatus.ACTIVE,
                )
            )
        ).scalar()
        or 0
    )

    total_completed_workouts = int(
        (
            await db.execute(
                select(func.count(WorkoutLog.id)).where(
                    WorkoutLog.client_id == client_record.id,
                    WorkoutLog.is_completed.is_(True),
                )
            )
        ).scalar()
        or 0
    )

    # Streak calculation: consecutive days with at least one completed workout
    workout_dates_stmt = (
        select(func.date(WorkoutLog.workout_date))
        .where(
            WorkoutLog.client_id == client_record.id,
            WorkoutLog.is_completed.is_(True),
        )
        .distinct()
        .order_by(func.date(WorkoutLog.workout_date).desc())
    )
    rows = (await db.execute(workout_dates_stmt)).all()

    def _to_date(d):
        if isinstance(d, str):
            return date.fromisoformat(d)
        return d

    current_streak = 0
    if rows:
        dates = [_to_date(row[0]) for row in rows if row[0]]
        if dates and dates[0] >= date.today() - timedelta(days=1):
            current_streak = 1
            for i in range(1, len(dates)):
                if dates[i - 1] - dates[i] == timedelta(days=1):
                    current_streak += 1
                else:
                    break

    return {
        "profile_completion": {
            "percentage": _calculate_profile_completion(client_record),
            "missing_fields": _missing_profile_fields(client_record),
        },
        "health_metrics": {
            "bmi": bmi,
            "weight": client_record.weight,
            "body_fat_percentage": client_record.body_fat_percentage,
        },
        "program_stats": {
            "active_programs": active_programs,
            "completed_workouts": total_completed_workouts,
            "current_streak": current_streak,
        },
    }


@router.get("/appointments")
async def get_client_appointments(
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    client_record = await ClientAccountService.get_client_by_user_id(db, current_user.id)
    if not client_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found"
        )

    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.trainer))
        .where(
            Appointment.client_id == client_record.id,
            Appointment.start_time >= datetime.utcnow(),
            Appointment.status.notin_(["cancelled"]),
        )
        .order_by(Appointment.start_time.asc())
        .limit(10)
    )
    appointments = list((await db.execute(stmt)).scalars().all())

    return {
        "appointments": [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "appointment_type": a.appointment_type,
                "status": a.status,
                "start_time": a.start_time.isoformat(),
                "end_time": a.end_time.isoformat(),
                "duration_minutes": a.duration_minutes,
                "location": a.location,
                "notes": a.notes,
                "trainer_name": (
                    f"{a.trainer.first_name} {a.trainer.last_name}" if a.trainer else None
                ),
            }
            for a in appointments
        ]
    }
