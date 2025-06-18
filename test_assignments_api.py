import requests
import json

# Test the assignments API
base_url = "http://localhost:8000"

# Login first to get token
login_data = {
    "email": "trainer@fitnesscoach.com",
    "password": "trainer123"
}

print("=== Testing Login ===")
response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
print(f"Login Status: {response.status_code}")

if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Assignments API ===")
    
    # Test getting all assignments
    response = requests.get(f"{base_url}/api/v1/assignments", headers=headers)
    print(f"All assignments Status: {response.status_code}")
    
    if response.status_code == 200:
        assignments = response.json()
        print(f"Found {len(assignments)} assignments")
        
        for assignment in assignments[:2]:  # Show first 2
            print(f"\nAssignment {assignment['id']}:")
            print(f"  Program: {assignment['program_name']}")
            print(f"  Client: {assignment['client_name']}")
            print(f"  Status: {assignment['status']}")
            print(f"  Has workout_structure: {'workout_structure' in assignment}")
            if 'workout_structure' in assignment and assignment['workout_structure']:
                structure = assignment['workout_structure']
                print(f"  Workout structure: {len(structure)} days")
                if structure:
                    first_day = structure[0]
                    print(f"    First day: {first_day.get('name', 'No name')}")
                    exercises = first_day.get('exercises', [])
                    print(f"    Exercises: {len(exercises)}")
                    if exercises:
                        first_exercise = exercises[0]
                        print(f"      First exercise: {first_exercise.get('exercise_name', 'No name')} ({first_exercise.get('exercise_id', 'No ID')})")
            else:
                print("  No workout structure")
    
    # Test filtering by client and status
    print("\n=== Testing Filtered Assignments ===")
    response = requests.get(f"{base_url}/api/v1/assignments?client_id=1&status=active", headers=headers)
    print(f"Filtered assignments Status: {response.status_code}")
    
    if response.status_code == 200:
        filtered_assignments = response.json()
        print(f"Found {len(filtered_assignments)} filtered assignments")
        
        for assignment in filtered_assignments:
            print(f"Assignment {assignment['id']}: {assignment['program_name']} -> {assignment['client_name']}")
            if 'workout_structure' in assignment and assignment['workout_structure']:
                print(f"  Has workout structure with {len(assignment['workout_structure'])} days")
    else:
        print(f"Error: {response.text}")
        
else:
    print(f"Login failed: {response.text}")
