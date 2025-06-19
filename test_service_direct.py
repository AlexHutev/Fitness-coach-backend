import sys
sys.path.append('.')

from app.services.appointment_service import AppointmentService
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.schedule import Appointment
from sqlalchemy.orm import Session
import sqlite3

def test_appointment_service():
    """Test the appointment service directly"""
    
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Get a trainer user
        trainer = db.query(User).filter(User.email == 'trainer@fitnesscoach.com').first()
        
        if not trainer:
            print("No trainer found")
            return
            
        print(f"Found trainer: {trainer.email}")
        
        # Test the service
        service = AppointmentService(db)
        appointments = service.get_todays_appointments(trainer.id)
        
        print(f"Found {len(appointments)} appointments")
        
        for apt in appointments:
            print(f"Appointment: {apt.title}")
            print(f"  Client: {apt.client.first_name if apt.client else 'No client'} {apt.client.last_name if apt.client else ''}")
            print(f"  Start: {apt.start_time}")
            print(f"  Status: {apt.status}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_appointment_service()
