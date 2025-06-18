import sqlite3
import json

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print('=== Program 1 workout structure ===')
cursor.execute('SELECT id, name, workout_structure FROM programs WHERE id = 1')
result = cursor.fetchone()
if result and result[2]:
    try:
        structure = json.loads(result[2])
        print(f'Program: {result[1]}')
        print(f'Structure: {json.dumps(structure, indent=2)}')
    except Exception as e:
        print(f'Error: {e}')

conn.close()
