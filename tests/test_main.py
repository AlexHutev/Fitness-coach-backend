"""Integration tests for the FitnessCoach API.

These tests use SQLite (aiosqlite) in-memory-per-file to exercise the async
SQLAlchemy session pipeline end-to-end. Rate limiting is disabled in tests
via the limiter's enabled flag so the auth-endpoint suite doesn't trip the
per-IP cap.
"""
import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def _override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db
limiter.enabled = False  # don't trip the per-IP cap during tests


@pytest_asyncio.fixture
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to FitnessCoach API"


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client, setup_database):
    user_data = {
        "email": "test@example.com",
        "password": "TestPass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
        "specialization": "personal-training",
        "experience": "intermediate",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == user_data["email"]
    assert "id" in body


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh_tokens(client, setup_database):
    user_data = {
        "email": "login@example.com",
        "password": "TestPass123",
        "first_name": "Login",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=user_data)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "TestPass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_issues_new_pair(client, setup_database):
    user_data = {
        "email": "refresh@example.com",
        "password": "TestPass123",
        "first_name": "Refresh",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "TestPass123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(client, setup_database):
    """An access token must not be accepted at the refresh endpoint."""
    user_data = {
        "email": "refresh-guard@example.com",
        "password": "TestPass123",
        "first_name": "Refresh",
        "last_name": "Guard",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh-guard@example.com", "password": "TestPass123"},
    )
    access_token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint(client, setup_database):
    user_data = {
        "email": "protected@example.com",
        "password": "TestPass123",
        "first_name": "Protected",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "protected@example.com", "password": "TestPass123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"


@pytest.mark.asyncio
async def test_create_client(client, setup_database):
    trainer_data = {
        "email": "trainer@example.com",
        "password": "TestPass123",
        "first_name": "Trainer",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=trainer_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "trainer@example.com", "password": "TestPass123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client_data = {
        "first_name": "John",
        "last_name": "Client",
        "email": "john@example.com",
        "primary_goal": "weight_loss",
    }
    response = await client.post("/api/v1/clients/", json=client_data, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "John"
    assert body["last_name"] == "Client"
