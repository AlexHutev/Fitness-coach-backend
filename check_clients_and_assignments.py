#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime

def check_system():
    conn = sqlite3.connect('fitness_coach.db')
    cursor = conn.cursor()
    
    print('=== SYSTEM STATUS CHECK ===')
    
    # Check users
    print('\n=== Users ===')
    cursor.execute('SELECT id, email, role, first_name, last_name FROM users')
    users = cursor.fetchall()
    for user in users:
        print(f'User {user[0]}: {user[1]} ({user[2]}) - {user[3]} {user[4]}')
    
    # Check clients  
    print('\n=== Clients ===')
    cursor.execute('''
        SELECT c.id, c.first_name, c.last_name, c.email, c.trainer_id, 
               u.first_name as trainer_fname, u.last_name as trainer_lname
        FROM clients c 
        LEFT JOIN users u ON c.trainer_id = u.id
    ''')
    clients = cursor.fetchall()
    for client in clients:
        print(f'Client {client[0]}: {client[1]} {client[2]} ({client[3]}) - Trainer: {client[5]} {client[6]} (ID: {client[4]})')
    
    # Check programs
    print('\n=== Programs ===')
    cursor.execute('SELECT id, name, trainer_id, program_type FROM programs')
    programs = cursor.fetchall()
    for program in programs:
        print(f'Program {program[0]}: {program[1]} (Type: {program[3]}, Trainer: {program[2]})')
    
    # Check program assignments
    print('\n=== Program Assignments ===')
    cursor.execute('''
        SELECT pa.id, pa.program_id, pa.client_id, pa.status, 
               p.name as program_name, c.first_name, c.last_name
        FROM program_assignments pa
        LEFT JOIN programs p ON pa.program_id = p.id
        LEFT JOIN clients c ON pa.client_id = c.id
    ''')
    assignments = cursor.fetchall()
    if assignments:
        for assignment in assignments:
            print(f'Assignment {assignment[0]}: Program "{assignment[4]}" -> Client {assignment[5]} {assignment[6]} (Status: {assignment[3]})')
    else:
        print('No program assignments found')
    
    # Check weekly exercises
    print('\n=== Weekly Exercise Assignments ===')
    cursor.execute('SELECT COUNT(*) FROM weekly_exercise_assignments')
    weekly_count = cursor.fetchone()[0]
    print(f'Total weekly exercise assignments: {weekly_count}')
    
    if weekly_count > 0:
        cursor.execute('''
            SELECT wea.id, wea.client_id, wea.exercise_id, wea.status, wea.week_number, wea.day_number,
                   c.first_name, c.last_name, e.name as exercise_name
            FROM weekly_exercise_assignments wea
            LEFT JOIN clients c ON wea.client_id = c.id
            LEFT JOIN exercises e ON wea.exercise_id = e.id
            LIMIT 10
        ''')
        weekly_exercises = cursor.fetchall()
        for we in weekly_exercises:
            print(f'Weekly Exercise {we[0]}: Client {we[6]} {we[7]} - Week {we[4]}, Day {we[5]} - {we[8]} (Status: {we[3]})')
    
    conn.close()

if __name__ == "__main__":
    check_system()
