#!/usr/bin/env python3

import sqlite3
from datetime import date, timedelta

def fix_weekly_exercise_dates():
    """Update weekly exercise due dates to current week"""
    conn = sqlite3.connect('fitness_coach.db')
    cursor = conn.cursor()
    
    print("Fixing weekly exercise due dates...")
    
    # Calculate current week
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    
    print(f"Today: {today}")
    print(f"Current week Monday: {week_start}")
    
    # Update exercises to current week
    cursor.execute("""
        UPDATE weekly_exercise_assignments 
        SET due_date = date(?, '+' || (day_number - 1) || ' days')
        WHERE client_id = 1
    """, (week_start.isoformat(),))
    
    updated_count = cursor.rowcount
    print(f"Updated {updated_count} exercise due dates")
    
    conn.commit()
    
    # Verify the update
    cursor.execute("""
        SELECT DISTINCT due_date, day_number
        FROM weekly_exercise_assignments 
        WHERE client_id = 1 
        ORDER BY day_number
    """)
    
    dates = cursor.fetchall()
    print("\nNew due dates:")
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for due_date, day_num in dates:
        day_name = day_names[day_num - 1] if day_num <= 7 else f"Day {day_num}"
        print(f"  {day_name}: {due_date}")
    
    conn.close()
    print("\nWeekly exercises updated to current week!")

if __name__ == "__main__":
    fix_weekly_exercise_dates()
