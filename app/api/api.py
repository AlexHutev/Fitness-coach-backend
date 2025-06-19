from fastapi import APIRouter
from app.api.endpoints import auth, clients, programs, exercises, assignments  # Remove appointments import
from app.api.endpoints import appointments_simple, simple_test
from app.api.endpoints import client as client_endpoint
from app.api.endpoints.client_dashboard import dashboard as client_dashboard

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(simple_test.router, prefix="/test", tags=["test"])
api_router.include_router(appointments_simple.router, prefix="/schedule", tags=["schedule"])  # Use different prefix
api_router.include_router(client_endpoint.router, tags=["client-access"])
api_router.include_router(client_dashboard.router, prefix="/client-dashboard", tags=["client-dashboard"])


@api_router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FitnessCoach API is running"}
