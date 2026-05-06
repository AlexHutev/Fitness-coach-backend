"""Async SQLAlchemy engine + session factories.

We keep one async engine for runtime (FastAPI request handlers) and one sync
engine for tooling that doesn't speak async — Alembic migrations and the
startup data seeder. Psycopg 3 supports both modes via the same DBAPI, so the
async URL is built by swapping the driver token in the configured DATABASE_URL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


def _async_url(url: str) -> str:
    # postgresql+psycopg works for both sync and async with psycopg3, but being
    # explicit about the +psycopg_async-style intent keeps the read clear and
    # protects us if someone configures a different sync driver later.
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL_ASYNC = _async_url(settings.database_url)
DATABASE_URL_SYNC = settings.database_url

# Async engine — used by the FastAPI app at request time.
async_engine = create_async_engine(
    DATABASE_URL_ASYNC,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.environment == "development",
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Sync engine — used by Alembic and the startup seeder.
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# SessionLocal kept as an alias so any tooling that still imports it works.
SessionLocal = SyncSessionLocal

Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI dependency yielding an AsyncSession scoped to the request."""
    async with AsyncSessionLocal() as session:
        yield session
