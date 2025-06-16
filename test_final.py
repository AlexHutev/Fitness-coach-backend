import requests

print('Testing program creation with fixed schema...')
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'trainer@fitnesscoach.com',
    'password': 'trainer123'
})

if response.status_code == 200:
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    prog_response = requests.post('http://localhost:8000/api/v1/programs/', 
                                 json={
                                     'name': 'Test Program', 
                                     'description': 'A test program', 
                                     'program_type': 'strength', 
                                     'difficulty_level': 'beginner', 
                                     'duration_weeks': 4, 
                                     'workout_structure': []
                                 },
                                 headers=headers)
    print(f'Status: {prog_response.status_code}')
    if prog_response.status_code == 201:
        result = prog_response.json()
        print('SUCCESS! Program created!')
        print(f'Program ID: {result.get("id")}')
        print(f'Name: {result.get("name")}')
        print(f'Type: {result.get("program_type")}')
        print(f'Difficulty: {result.get("difficulty_level")}')
    else:
        print(f'Error: {prog_response.text}')
else:
    print(f'Login failed: {response.text}')
