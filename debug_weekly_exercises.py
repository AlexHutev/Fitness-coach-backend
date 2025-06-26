#!/usr/bin/env python3

import sqlite3
from datetime import date, timedelta

def check_weekly_exercises():
    conn = sqlite3.connect('fitness_coach.db')
    cursor = conn.cursor()
    
    print("=== Weekly Exercise Details ===")
    
    # Check all weekly exercises for client 1
    cursor.execute("""
        SELECT wea.id, wea.client_id, wea.exercise_id, wea.week_number, wea.day_number,
               wea.due_date, wea.status, e.name as exercise_name
        FROM weekly_exercise_assignments wea
        LEFT JOIN exercises e ON wea.exercise_id = e.id
        WHERE wea.client_id = 1
        ORDER BY wea.week_number, wea.day_number, wea.exercise_order
        LIMIT 20
    """)
    
    exercises = cursor.fetchall()
    
    print(f"Found {len(exercises)} weekly exercises for client 1:")
    
    for exercise in exercises:
        print(f"  ID {exercise[0]}: Week {exercise[3]}, Day {exercise[4]} - {exercise[7]} (Due: {exercise[5]}, Status: {exercise[6]})")
    
    # Check current week calculation
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    week_end = week_start + timedelta(days=6)
    
    print(f"\nCurrent week calculation:")
    print(f"Today: {today}")
    print(f"Week start (Monday): {week_start}")
    print(f"Week end (Sunday): {week_end}")
    
    # Check exercises in current week
    cursor.execute("""
        SELECT COUNT(*) 
        FROM weekly_exercise_assignments wea
        WHERE wea.client_id = 1 
        AND wea.due_date >= ? 
        AND wea.due_date <= ?
    """, (week_start.isoformat(), week_end.isoformat()))
    
    current_week_count = cursor.fetchone()[0]
    print(f"Exercises in current week: {current_week_count}")
    
    # Check all due dates
    cursor.execute("""
        SELECT DISTINCT due_date 
        FROM weekly_exercise_assignments 
        WHERE client_id = 1 
        ORDER BY due_date
    """)
    
    due_dates = cursor.fetchall()
    print(f"\nAll due dates for client 1:")
    for due_date in due_dates:
        print(f"  {due_date[0]}")
    
    conn.close()

if __name__ == "__main__":
    check_weekly_exercises()
