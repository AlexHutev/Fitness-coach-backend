import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.rate_limit import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all models so SQLAlchemy registers their tables before engines connect.
from app.models.user import User  # noqa: E402,F401
from app.models.client import Client  # noqa: E402,F401
from app.models.program import Exercise, Program  # noqa: E402,F401
from app.models.program_assignment import ProgramAssignment  # noqa: E402,F401
from app.models.workout_tracking import ExerciseLog, WorkoutLog  # noqa: E402,F401
from app.models.weekly_exercise import WeeklyExerciseAssignment  # noqa: E402,F401
from app.models.nutrition import Food, NutritionPlan  # noqa: E402,F401
from app.models.schedule import Appointment  # noqa: E402,F401
from app.models.notification import Notification  # noqa: E402,F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FitnessCoach API starting up...")
    logger.info("Environment: %s", settings.environment)
    db_url = settings.database_url
    logger.info(
        "Database: %s",
        db_url.split("@", 1)[1] if "@" in db_url else "Not configured",
    )

    # Schema is owned by Alembic — run `alembic upgrade head` before starting.
    # We do, however, seed sample exercises on first boot so a fresh DB has
    # something to demo. The seeder is sync; the async engine isn't suitable
    # for one-off blocking startup work, so we use the sync SessionLocal here.
    try:
        from app.core.database import SessionLocal
        from app.core.sample_data import seed_sample_exercises

        with SessionLocal() as db:
            seed_sample_exercises(db)
    except Exception as e:
        logger.error("Error seeding sample data: %s", e)

    yield

    logger.info("FitnessCoach API shutting down...")


app = FastAPI(
    title="FitnessCoach API",
    description="API for fitness coaches to manage clients, training programs, and nutrition plans",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter — slowapi attaches the limiter to app.state and registers a
# 429 exception handler so decorated routes return a clean JSON error.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — origins are configurable via ALLOWED_ORIGINS in .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log first, then re-raise so Starlette's default 500 handler responds.
    # That path routes through the CORS middleware, so the browser sees the
    # Access-Control-Allow-Origin header instead of a CORS-blocked response
    # that would mask the real error.
    logger.exception(
        "Unhandled exception during request: %s %s", request.method, request.url.path
    )
    raise exc


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to FitnessCoach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )
