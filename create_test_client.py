"""
Simple test to create client credentials manually
"""

import sqlite3
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_test_client():
    # Connect to database
    conn = sqlite3.connect('C:/university/fitness-coach/fitness_coach.db')
    cursor = conn.cursor()
    
    try:
        # Check if we have a trainer
        cursor.execute("SELECT id FROM users WHERE email = ?", ("trainer@fitnesscoach.com",))
        trainer = cursor.fetchone()
        
        if not trainer:
            print("No trainer found")
            return
        
        trainer_id = trainer[0]
        print(f"Found trainer with ID: {trainer_id}")
        
        # Get first client
        cursor.execute("SELECT id, first_name, last_name FROM clients WHERE trainer_id = ? LIMIT 1", (trainer_id,))
        client = cursor.fetchone()
        
        if not client:
            print("No clients found")
            return
        
        client_id, first_name, last_name = client
        print(f"Found client: {first_name} {last_name} (ID: {client_id})")
        
        # Get first program
        cursor.execute("SELECT id, name FROM programs WHERE trainer_id = ? LIMIT 1", (trainer_id,))
        program = cursor.fetchone()
        
        if not program:
            print("No programs found")
            return
        
        program_id, program_name = program
        print(f"Found program: {program_name} (ID: {program_id})")
        
        # Create assignment
        start_date = datetime.now()
        end_date = start_date + timedelta(weeks=8)
        
        cursor.execute("""
            INSERT OR REPLACE INTO program_assignments 
            (trainer_id, client_id, program_id, start_date, end_date, 
             assignment_notes, total_workouts, completed_workouts, 
             client_access_email, client_hashed_password, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trainer_id, client_id, program_id, start_date, end_date,
            f"Test assignment for {first_name}", 24, 0,
            f"{first_name.lower()}@client.com", 
            hash_password("client123"),
            datetime.now()
        ))
        
        conn.commit()
        
        print("\n" + "="*50)
        print("[OK] Test client assignment created successfully!")
        print("\nClient Login Credentials:")
        print(f"Email: {first_name.lower()}@client.com")
        print("Password: client123")
        print(f"Program: {program_name}")
        print("\nYou can now test at: http://localhost:3001/client/login")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_test_client()