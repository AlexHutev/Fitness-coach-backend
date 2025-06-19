import sqlite3
import json
from datetime import datetime, timedelta

# Test script to verify appointments are working
def test_appointments():
    """Test the appointments functionality"""
    
    # Connect to database
    conn = sqlite3.connect('C:/university/fitness-coach/fitness_coach.db')
    cursor = conn.cursor()
    
    try:
        # Check if appointments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("Appointments table exists")
            
            # Check appointments data
            cursor.execute("SELECT COUNT(*) FROM appointments")
            count = cursor.fetchone()[0]
            print(f"Total appointments: {count}")
            
            # Get today's appointments
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT a.*, c.first_name, c.last_name 
                FROM appointments a 
                JOIN clients c ON a.client_id = c.id 
                WHERE DATE(a.start_time) = ?
                ORDER BY a.start_time
            """, (today,))
            
            appointments = cursor.fetchall()
            
            print(f"\nToday's appointments ({len(appointments)}):")
            for apt in appointments:
                start_time = datetime.fromisoformat(apt[7]).strftime('%H:%M')
                client_name = f"{apt[14]} {apt[15]}"
                print(f"  - {start_time} - {client_name} ({apt[5]})")
                print(f"    Status: {apt[6]} | Location: {apt[10] or 'Not specified'}")
            
            # Check trainer and client relationships
            cursor.execute("""
                SELECT COUNT(DISTINCT trainer_id) as trainers,
                       COUNT(DISTINCT client_id) as clients
                FROM appointments
            """)
            stats = cursor.fetchone()
            print(f"\nAppointment stats:")
            print(f"  - Trainers with appointments: {stats[0]}")
            print(f"  - Clients with appointments: {stats[1]}")
            
        else:
            print("Appointments table not found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing Appointments Functionality\n")
    test_appointments()
    print("\nTest completed!")
