#!/usr/bin/env python3

import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print("=== PROGRAMS TABLE ===")
cursor.execute("SELECT id, name, trainer_id, program_type, difficulty_level, workout_structure FROM programs")
programs = cursor.fetchall()

for program in programs:
    program_id, name, trainer_id, program_type, difficulty_level, workout_structure = program
    print(f"Program ID: {program_id}")
    print(f"Name: {name}")
    print(f"Trainer ID: {trainer_id}")
    print(f"Type: {program_type}")
    print(f"Difficulty: {difficulty_level}")
    print(f"Workout Structure: {workout_structure}")
    print("-" * 50)

print("\n=== USERS TABLE ===")
cursor.execute("SELECT id, email, first_name, last_name FROM users")
users = cursor.fetchall()

for user in users:
    user_id, email, first_name, last_name = user
    print(f"User ID: {user_id}, Email: {email}, Name: {first_name} {last_name}")

conn.close()
