from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import ProgramAssignment
from app.schemas.client_schemas import (
    ClientDashboardResponse,
    ClientLoginRequest,
    ClientTokenResponse,
    ProgramTemplateForClient,
    WorkoutLogCreate,
    WorkoutLogResponse,
)
from app.services.client_auth_service import client_auth_service
from app.services.client_dashboard_service import client_dashboard_service
from app.services.workout_tracking_service import workout_tracking_service

router = APIRouter(prefix="/client", tags=["client"])
security = HTTPBearer()


async def get_current_client_assignment(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> ProgramAssignment:
    assignment = await client_auth_service.get_client_assignment_from_token(
        db, credentials.credentials
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return assignment


@router.post("/login", response_model=ClientTokenResponse)
async def login_client(
    login_request: ClientLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    token_response = await client_auth_service.login_client(db, login_request)
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return token_response


@router.get("/dashboard", response_model=ClientDashboardResponse)
async def get_client_dashboard(
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    dashboard = await client_dashboard_service.get_client_dashboard(
        db, assignment.client_id
    )
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client data not found"
        )
    return dashboard


@router.get("/program", response_model=ProgramTemplateForClient)
async def get_assigned_program(
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    template = await client_dashboard_service.get_program_template_for_client(
        db, assignment.id
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
        )
    return template


@router.post("/workout", response_model=WorkoutLogResponse)
async def log_workout(
    workout_data: WorkoutLogCreate,
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    if workout_data.assignment_id != assignment.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot log workout for a different assignment",
        )
    workout_log = await workout_tracking_service.create_workout_log(
        db, workout_data, assignment.client_id
    )
    if not workout_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create workout log",
        )
    return workout_log


@router.get("/workouts", response_model=List[WorkoutLogResponse])
async def get_workout_history(
    limit: int = 20,
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    return await workout_tracking_service.get_workout_logs_for_assignment(
        db, assignment.id, assignment.client_id, limit
    )


@router.get("/workout/{workout_id}", response_model=WorkoutLogResponse)
async def get_workout_details(
    workout_id: int,
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    workout = await workout_tracking_service.get_workout_log(
        db, workout_id, assignment.client_id
    )
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )
    return workout


@router.put("/workout/{workout_id}", response_model=WorkoutLogResponse)
async def update_workout(
    workout_id: int,
    update_data: dict,
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    workout = await workout_tracking_service.update_workout_log(
        db, workout_id, assignment.client_id, update_data
    )
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )
    return workout


@router.get("/progress/summary")
async def get_progress_summary(
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
    db: AsyncSession = Depends(get_db),
):
    return await workout_tracking_service.get_workout_history_summary(
        db, assignment.id, assignment.client_id
    )


@router.get("/me")
async def get_client_info(
    assignment: ProgramAssignment = Depends(get_current_client_assignment),
):
    return {
        "client_id": assignment.client_id,
        "assignment_id": assignment.id,
        "program_id": assignment.program_id,
        "start_date": assignment.start_date,
        "status": assignment.status.value,
        "completed_workouts": assignment.completed_workouts,
        "total_workouts": assignment.total_workouts,
    }
