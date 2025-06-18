import sqlite3
import json

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print('=== Program Assignments ===')
cursor.execute('SELECT id, program_id, client_id, status FROM program_assignments WHERE status = ? LIMIT 5', ('active',))
assignments = cursor.fetchall()
for assignment in assignments:
    print(f'Assignment {assignment[0]}: Program {assignment[1]} -> Client {assignment[2]} (Status: {assignment[3]})')

print('\n=== Programs with Workout Structure ===')
cursor.execute('SELECT id, name, workout_structure FROM programs WHERE workout_structure IS NOT NULL LIMIT 3')
programs = cursor.fetchall()
for program in programs:
    print(f'Program {program[0]}: {program[1]}')
    if program[2]:
        try:
            structure = json.loads(program[2])
            if isinstance(structure, list) and len(structure) > 0:
                first_day = structure[0]
                print(f'  First day: {first_day.get("name", "Unknown")}')
                if 'exercises' in first_day and len(first_day['exercises']) > 0:
                    first_exercise = first_day['exercises'][0]
                    print(f'  First exercise: {first_exercise}')
        except Exception as e:
            print(f'  Error parsing structure: {e}')

print('\n=== Exercise Names ===')
cursor.execute('SELECT id, name FROM exercises LIMIT 5')
exercises = cursor.fetchall()
for exercise in exercises:
    print(f'Exercise {exercise[0]}: {exercise[1]}')

conn.close()
