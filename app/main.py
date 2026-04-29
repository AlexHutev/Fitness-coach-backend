from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.api import api_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all models at module level to register them with SQLAlchemy
from app.models.user import User
from app.models.client import Client
from app.models.program import Program, Exercise
from app.models.program_assignment import ProgramAssignment
from app.models.workout_tracking import WorkoutLog, ExerciseLog
from app.models.weekly_exercise import WeeklyExerciseAssignment
from app.models.nutrition import NutritionPlan, Food
from app.models.schedule import Appointment
from app.models.notification import Notification


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FitnessCoach API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(
        f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Not configured'}"
    )

    # Schema is managed by Alembic — run `alembic upgrade head` before starting the app.
    try:
        from app.core.database import SessionLocal
        from app.core.sample_data import seed_sample_exercises
        with SessionLocal() as db:
            seed_sample_exercises(db)
    except Exception as e:
        logger.error(f"Error seeding sample data: {e}")

    yield

    logger.info("FitnessCoach API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="FitnessCoach API",
    description="API for fitness coaches to manage clients, training programs, and nutrition plans",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log first…
    logger.exception("Unhandled exception during request: %s %s", request.method, request.url.path)
    # …then re-raise so Starlette's default 500 handler responds. That path
    # routes through the CORS middleware, so the browser sees the
    # Access-Control-Allow-Origin header instead of a CORS-blocked response
    # that would mask the real error.
    raise exc


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to FitnessCoach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
