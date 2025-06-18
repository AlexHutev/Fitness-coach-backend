import sqlite3
import json

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print('=== All Program Assignments ===')
cursor.execute('SELECT id, program_id, client_id, status FROM program_assignments LIMIT 10')
assignments = cursor.fetchall()
if not assignments:
    print('No assignments found!')
else:
    for assignment in assignments:
        print(f'Assignment {assignment[0]}: Program {assignment[1]} -> Client {assignment[2]} (Status: {assignment[3]})')

print('\n=== All Clients ===')
cursor.execute('SELECT id, first_name, last_name FROM clients LIMIT 5')
clients = cursor.fetchall()
for client in clients:
    print(f'Client {client[0]}: {client[1]} {client[2]}')

print('\n=== Checking program structure for Program 2 ===')
cursor.execute('SELECT workout_structure FROM programs WHERE id = 2')
result = cursor.fetchone()
if result and result[0]:
    try:
        structure = json.loads(result[0])
        for day in structure[:2]:  # Show first 2 days
            print(f'Day {day["day"]}: {day["name"]}')
            for i, exercise in enumerate(day["exercises"][:2]):  # Show first 2 exercises
                print(f'  Exercise {i+1}: {exercise}')
    except Exception as e:
        print(f'Error: {e}')

conn.close()
