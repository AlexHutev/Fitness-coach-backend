import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "fitness_coach.db"

def add_appointments_table():
    """Add appointments table to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainer_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                appointment_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'scheduled',
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                duration_minutes INTEGER NOT NULL DEFAULT 60,
                location VARCHAR(200),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trainer_id) REFERENCES users (id),
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_trainer_id ON appointments(trainer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_client_id ON appointments(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
        
        conn.commit()
        print("Appointments table created successfully!")
        
        # Add some sample appointments
        add_sample_appointments(cursor)
        conn.commit()
        print("Sample appointments added!")
        
    except Exception as e:
        print(f"Error creating appointments table: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_sample_appointments(cursor):
    """Add sample appointments for testing"""
    
    # Get trainer and client IDs
    cursor.execute("SELECT id FROM users WHERE email = 'trainer@fitnesscoach.com'")
    trainer_result = cursor.fetchone()
    if not trainer_result:
        print("Trainer not found, skipping sample appointments")
        return
    
    trainer_id = trainer_result[0]
    
    # Get some client IDs
    cursor.execute("SELECT id, first_name, last_name FROM clients WHERE trainer_id = ? LIMIT 4", (trainer_id,))
    clients = cursor.fetchall()
    
    if not clients:
        print("No clients found, skipping sample appointments")
        return
    
    from datetime import datetime, timedelta
    
    # Create appointments for today
    today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    
    sample_appointments = [
        {
            'trainer_id': trainer_id,
            'client_id': clients[0][0],
            'title': f'Personal Training - {clients[0][1]} {clients[0][2]}',
            'description': 'Upper body strength training session',
            'appointment_type': 'Personal Training',
            'status': 'confirmed',
            'start_time': today,
            'end_time': today + timedelta(hours=1),
            'duration_minutes': 60,
            'location': 'Main Gym Floor',
            'notes': 'Focus on proper form and progressive overload'
        },
        {
            'trainer_id': trainer_id,
            'client_id': clients[1][0] if len(clients) > 1 else clients[0][0],
            'title': f'Program Review - {clients[1][1] if len(clients) > 1 else clients[0][1]} {clients[1][2] if len(clients) > 1 else clients[0][2]}',
            'description': 'Monthly program assessment and adjustments',
            'appointment_type': 'Program Review',
            'status': 'confirmed',
            'start_time': today + timedelta(hours=2),
            'end_time': today + timedelta(hours=2, minutes=30),
            'duration_minutes': 30,
            'location': 'Consultation Room',
            'notes': 'Review progress and update program'
        },
        {
            'trainer_id': trainer_id,
            'client_id': clients[2][0] if len(clients) > 2 else clients[0][0],
            'title': f'Initial Assessment - {clients[2][1] if len(clients) > 2 else clients[0][1]} {clients[2][2] if len(clients) > 2 else clients[0][2]}',
            'description': 'Comprehensive fitness assessment for new client',
            'appointment_type': 'Initial Assessment',
            'status': 'pending',
            'start_time': today + timedelta(hours=5),
            'end_time': today + timedelta(hours=6),
            'duration_minutes': 60,
            'location': 'Assessment Room',
            'notes': 'Include body composition analysis and movement screening'
        },
        {
            'trainer_id': trainer_id,
            'client_id': clients[3][0] if len(clients) > 3 else clients[0][0],
            'title': f'Personal Training - {clients[3][1] if len(clients) > 3 else clients[0][1]} {clients[3][2] if len(clients) > 3 else clients[0][2]}',
            'description': 'Lower body strength and conditioning',
            'appointment_type': 'Personal Training',
            'status': 'confirmed',
            'start_time': today + timedelta(hours=7),
            'end_time': today + timedelta(hours=8),
            'duration_minutes': 60,
            'location': 'Main Gym Floor',
            'notes': 'Focus on compound movements and mobility'
        }
    ]
    
    for appointment in sample_appointments:
        cursor.execute("""
            INSERT INTO appointments (
                trainer_id, client_id, title, description, appointment_type,
                status, start_time, end_time, duration_minutes, location, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            appointment['trainer_id'],
            appointment['client_id'],
            appointment['title'],
            appointment['description'],
            appointment['appointment_type'],
            appointment['status'],
            appointment['start_time'].isoformat(),
            appointment['end_time'].isoformat(),
            appointment['duration_minutes'],
            appointment['location'],
            appointment['notes']
        ))

if __name__ == "__main__":
    add_appointments_table()