import sqlite3

conn = sqlite3.connect('fitness_coach.db')
cursor = conn.cursor()

print('=== Assignment Details ===')
cursor.execute('''
SELECT pa.id, pa.client_id, pa.status,
       c.first_name, c.last_name,
       p.id as program_id, p.name as program_name
FROM program_assignments pa
JOIN clients c ON pa.client_id = c.id
JOIN programs p ON pa.program_id = p.id
WHERE pa.status = 'ACTIVE'
''')

assignments = cursor.fetchall()
for assignment in assignments:
    print(f'Assignment {assignment[0]}: Program {assignment[5]} ({assignment[6]}) -> Client {assignment[1]} ({assignment[3]} {assignment[4]}) - Status: {assignment[2]}')

conn.close()
