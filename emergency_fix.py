#!/usr/bin/env python3
"""
Emergency fix - create database using raw SQL
"""
import sqlite3
import os
import hashlib
from datetime import datetime
import json

def simple_hash_password(password):
    """Simple password hashing for demo"""
    return f"$2b$12$demo.{hashlib.sha256(password.encode()).hexdigest()[:50]}"

def create_emergency_database():
    """Create database using raw SQLite commands"""
    
    db_path = "fitness_coach.db"
    
    # Delete existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20),
                hashed_password VARCHAR(255) NOT NULL,
                specialization VARCHAR(50),
                experience VARCHAR(20),
                bio TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                role VARCHAR(10) DEFAULT 'TRAINER',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                last_login DATETIME
            )
        """)
        
        # Create clients table
        cursor.execute("""
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY,
                trainer_id INTEGER NOT NULL,
                user_id INTEGER,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                phone_number VARCHAR(20),
                date_of_birth DATETIME,
                gender VARCHAR(10),
                height FLOAT,
                weight FLOAT,
                body_fat_percentage FLOAT,
                activity_level VARCHAR(20),
                primary_goal VARCHAR(20),
                secondary_goals TEXT,
                medical_conditions TEXT,
                injuries TEXT,
                emergency_contact_name VARCHAR(100),
                emergency_contact_phone VARCHAR(20),
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(trainer_id) REFERENCES users(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Create programs table
        cursor.execute("""
            CREATE TABLE programs (
                id INTEGER PRIMARY KEY,
                trainer_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                program_type VARCHAR(20) NOT NULL,
                difficulty_level VARCHAR(15) NOT NULL,
                duration_weeks INTEGER,
                sessions_per_week INTEGER,
                workout_structure JSON,
                tags TEXT,
                equipment_needed TEXT,
                is_template BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(trainer_id) REFERENCES users(id)
            )
        """)
        
        # Create program_assignments table
        cursor.execute("""
            CREATE TABLE program_assignments (
                id INTEGER PRIMARY KEY,
                program_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                start_date DATETIME,
                end_date DATETIME,
                status VARCHAR(10) DEFAULT 'ACTIVE',
                client_access_email VARCHAR(255),
                client_hashed_password VARCHAR(255),
                custom_notes TEXT,
                trainer_notes TEXT,
                assignment_notes TEXT,
                trainer_feedback TEXT,
                completion_percentage INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                total_sessions INTEGER,
                total_workouts INTEGER DEFAULT 0,
                completed_workouts INTEGER DEFAULT 0,
                last_workout_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(program_id) REFERENCES programs(id),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(trainer_id) REFERENCES users(id)
            )
        """)
        
        # Create exercises table (minimal)
        cursor.execute("""
            CREATE TABLE exercises (
                id INTEGER PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                instructions TEXT,
                muscle_groups TEXT,
                equipment TEXT,
                difficulty_level VARCHAR(20),
                image_url VARCHAR(500),
                video_url VARCHAR(500),
                created_by INTEGER,
                is_public BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """)
        
        print("✅ Tables created successfully!")
        
        # Insert trainer
        trainer_password = simple_hash_password("trainer123")
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name, hashed_password, role, is_active, is_verified)
            VALUES (1, 'trainer@fitnesscoach.com', 'John', 'Trainer', ?, 'TRAINER', 1, 1)
        """, (trainer_password,))
        
        # Insert client user
        client_password = simple_hash_password("client123")
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name, hashed_password, role, is_active, is_verified)
            VALUES (2, 'john.doe@client.com', 'John', 'Doe', ?, 'CLIENT', 1, 1)
        """, (client_password,))
        
        # Insert client profile
        cursor.execute("""
            INSERT INTO clients (id, trainer_id, user_id, first_name, last_name, email, height, weight, gender, primary_goal, activity_level)
            VALUES (1, 1, 2, 'John', 'Doe', 'john.doe@client.com', 180, 75, 'MALE', 'WEIGHT_LOSS', 'MODERATELY_ACTIVE')
        """)
        
        # Insert program
        workout_structure = [
            {
                "day": 1,
                "name": "Day 1",
                "exercises": [
                    {
                        "exercise_id": 1,
                        "exercise_name": "Push-ups",
                        "sets": 3,
                        "reps": "10-15",
                        "weight": "bodyweight",
                        "rest_seconds": 60,
                        "notes": "Keep your core tight"
                    },
                    {
                        "exercise_id": 2,
                        "exercise_name": "Squats", 
                        "sets": 3,
                        "reps": "12-15",
                        "weight": "bodyweight",
                        "rest_seconds": 90,
                        "notes": "Go down until thighs are parallel"
                    }
                ]
            },
            {
                "day": 2,
                "name": "Day 2", 
                "exercises": [
                    {
                        "exercise_id": 3,
                        "exercise_name": "Lunges",
                        "sets": 3,
                        "reps": "10 each leg",
                        "weight": "bodyweight",
                        "rest_seconds": 60,
                        "notes": "Alternate legs"
                    }
                ]
            },
            {
                "day": 3,
                "name": "Day 3",
                "exercises": [
                    {
                        "exercise_id": 4,
                        "exercise_name": "Plank",
                        "sets": 3,
                        "reps": "30-60 seconds",
                        "weight": "bodyweight",
                        "rest_seconds": 60,
                        "notes": "Keep body in straight line"
                    }
                ]
            }
        ]
        
        cursor.execute("""
            INSERT INTO programs (id, trainer_id, name, description, program_type, difficulty_level, duration_weeks, workout_structure)
            VALUES (1, 1, 'Mobility & Core Reset', 'A gentle 4-week program for beginners', 'Strength', 'Beginner', 4, ?)
        """, (json.dumps(workout_structure),))
        
        # Insert program assignment
        cursor.execute("""
            INSERT INTO program_assignments (id, program_id, client_id, trainer_id, status, completion_percentage, total_workouts, completed_workouts)
            VALUES (1, 1, 1, 1, 'ACTIVE', 0, 3, 0)
        """)
        
        conn.commit()
        
        print("✅ SUCCESS! Database created with demo data!")
        print("\n📝 Login Credentials:")
        print("👨‍💼 Trainer: trainer@fitnesscoach.com / trainer123")
        print("👤 Client: john.doe@client.com / client123")
        print("\n🌐 Ready to test at http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_emergency_database()
