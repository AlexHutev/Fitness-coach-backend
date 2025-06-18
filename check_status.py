import sqlite3

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print('=== Assignment Status Values ===')
cursor.execute('SELECT DISTINCT status FROM program_assignments')
statuses = cursor.fetchall()
for status in statuses:
    print(f'Status: "{status[0]}" (type: {type(status[0])})')

print('\n=== Assignments by status ===')
cursor.execute('SELECT id, status FROM program_assignments')
assignments = cursor.fetchall()
for assignment in assignments:
    print(f'Assignment {assignment[0]}: status = "{assignment[1]}"')

conn.close()
