from fastapi import APIRouter, Depends
from app.utils.deps import get_current_trainer
from app.models.user import User

router = APIRouter()

@router.get("/")
def get_appointments_simple(
    today_only: bool = False,
    current_user: User = Depends(get_current_trainer)
):
    """Simple appointments endpoint that returns static data for now"""
    
    # Return static appointments data for testing
    appointments_data = [
        {
            "id": 1,
            "title": "Personal Training - John Smith",
            "appointment_type": "Personal Training",
            "status": "confirmed",
            "start_time": "2025-06-19T09:00:00",
            "end_time": "2025-06-19T10:00:00",
            "location": "Main Gym Floor",
            "client": {
                "id": 1,
                "first_name": "John",
                "last_name": "Smith"
            }
        },
        {
            "id": 2,
            "title": "Program Review - Maria Petrova", 
            "appointment_type": "Program Review",
            "status": "confirmed",
            "start_time": "2025-06-19T11:00:00",
            "end_time": "2025-06-19T11:30:00",
            "location": "Consultation Room",
            "client": {
                "id": 2,
                "first_name": "Maria",
                "last_name": "Petrova"
            }
        },
        {
            "id": 3,
            "title": "Initial Assessment - Adi Hadzhiev",
            "appointment_type": "Initial Assessment", 
            "status": "pending",
            "start_time": "2025-06-19T14:00:00",
            "end_time": "2025-06-19T15:00:00",
            "location": "Assessment Room",
            "client": {
                "id": 3,
                "first_name": "Adi",
                "last_name": "Hadzhiev"
            }
        },
        {
            "id": 4,
            "title": "Personal Training - TestClient WithPassword",
            "appointment_type": "Personal Training",
            "status": "confirmed", 
            "start_time": "2025-06-19T16:00:00",
            "end_time": "2025-06-19T17:00:00",
            "location": "Main Gym Floor",
            "client": {
                "id": 4,
                "first_name": "TestClient",
                "last_name": "WithPassword"
            }
        }
    ]
    
    if today_only:
        return {
            "appointments": appointments_data,
            "total": len(appointments_data),
            "page": 1,
            "size": len(appointments_data)
        }
    else:
        return {
            "appointments": appointments_data,
            "total": len(appointments_data),
            "page": 1,
            "size": len(appointments_data)
        }

@router.get("/test")
def test_appointments_endpoint(current_user: User = Depends(get_current_trainer)):
    """Simple test endpoint"""
    return {"message": "Appointments endpoint is working", "user": current_user.email}
