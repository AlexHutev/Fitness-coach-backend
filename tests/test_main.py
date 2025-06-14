import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
import tempfile
import os

# Create a temporary database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to FitnessCoach API"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(setup_database):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "TestPass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
        "specialization": "personal-training",
        "experience": "intermediate"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
    assert "id" in response.json()


def test_login_user(setup_database):
    """Test user login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "TestPass123",
        "first_name": "Login",
        "last_name": "User"
    }
    
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "email": "login@example.com",
        "password": "TestPass123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_protected_endpoint(setup_database):
    """Test accessing protected endpoint"""
    # Register and login to get token
    user_data = {
        "email": "protected@example.com",
        "password": "TestPass123",
        "first_name": "Protected",
        "last_name": "User"
    }
    
    client.post("/api/v1/auth/register", json=user_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "email": "protected@example.com",
        "password": "TestPass123"
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Access protected endpoint
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"


def test_create_client(setup_database):
    """Test creating a client"""
    # Register and login as trainer
    trainer_data = {
        "email": "trainer@example.com",
        "password": "TestPass123",
        "first_name": "Trainer",
        "last_name": "User"
    }
    
    client.post("/api/v1/auth/register", json=trainer_data)
    
    login_response = client.post("/api/v1/auth/login", json={
        "email": "trainer@example.com",
        "password": "TestPass123"
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create client
    client_data = {
        "first_name": "John",
        "last_name": "Client",
        "email": "john@example.com",
        "primary_goal": "weight_loss"
    }
    
    response = client.post("/api/v1/clients/", json=client_data, headers=headers)
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
    assert response.json()["last_name"] == "Client"


if __name__ == "__main__":
    pytest.main([__file__])
