import sqlite3
import json

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

# Find programs with non-empty workout structure
cursor.execute('SELECT id, name, workout_structure FROM programs WHERE workout_structure IS NOT NULL AND workout_structure != "[]" LIMIT 3')
programs = cursor.fetchall()

for program in programs:
    print(f'\n=== Program {program[0]}: {program[1]} ===')
    if program[2]:
        try:
            structure = json.loads(program[2])
            if structure:
                print(f'Structure (first day): {json.dumps(structure[0], indent=2)}')
            else:
                print('Empty structure')
        except Exception as e:
            print(f'Error: {e}')

conn.close()
