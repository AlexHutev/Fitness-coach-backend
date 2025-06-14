from fastapi import APIRouter
from app.api.endpoints import auth, clients, programs, exercises

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])


@api_router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FitnessCoach API is running"}
