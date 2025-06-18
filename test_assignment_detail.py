import requests
import json

# Test specific assignment
base_url = "http://localhost:8000"

# Login first to get token
login_data = {
    "email": "trainer@fitnesscoach.com",
    "password": "trainer123"
}

response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== Testing Assignment 1 Details ===")
    response = requests.get(f"{base_url}/api/v1/assignments/1", headers=headers)
    print(f"Assignment 1 Status: {response.status_code}")
    
    if response.status_code == 200:
        assignment = response.json()
        print(f"Assignment: {assignment['program_name']} -> {assignment['client_name']}")
        print(f"Status: {assignment['status']}")
        print(f"Has workout_structure: {'workout_structure' in assignment}")
        if 'workout_structure' in assignment and assignment['workout_structure']:
            structure = assignment['workout_structure']
            print(f"Workout structure: {len(structure)} days")
            for day in structure:
                print(f"  Day {day['day']}: {day['name']} - {len(day.get('exercises', []))} exercises")
        else:
            print("No workout structure")
    else:
        print(f"Error: {response.text}")
