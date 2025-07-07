#!/usr/bin/env python3

import requests
import json

# Login to get token
login_data = {
    "email": "admin@fitnesscoach.com",
    "password": "admin123"
}

print("Logging in...")
response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"Got token: {token[:20]}...")
    
    # Test getting the program first
    headers = {"Authorization": f"Bearer {token}"}
    print("\nGetting program 5...")
    get_response = requests.get("http://localhost:8000/api/v1/programs/5", headers=headers)
    print(f"Get status: {get_response.status_code}")
    
    if get_response.status_code == 200:
        program_data = get_response.json()
        print(f"Program name: {program_data['name']}")
        print(f"Workout structure: {len(program_data['workout_structure'])} days")
        
        # Try to update the program
        update_data = {
            "name": "Test2 - Updated",
            "description": "Updated description",
            "workout_structure": program_data["workout_structure"]
        }
        
        print("\nUpdating program...")
        put_response = requests.put(
            "http://localhost:8000/api/v1/programs/5", 
            json=update_data,
            headers=headers
        )
        print(f"Update status: {put_response.status_code}")
        print(f"Update response: {put_response.text}")
        
    else:
        print(f"Failed to get program: {get_response.text}")
        
else:
    print(f"Login failed: {response.text}")
