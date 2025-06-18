#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_exercises_api():
    """Test the exercises API endpoint"""
    
    # First login to get a token
    login_data = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return False
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test exercises endpoint
    exercises_response = requests.get("http://localhost:8000/api/v1/exercises/", headers=headers)
    if exercises_response.status_code != 200:
        print(f"Exercises API failed: {exercises_response.status_code}")
        print(exercises_response.text)
        return False
        
    exercises = exercises_response.json()
    print(f"Successfully fetched {len(exercises)} exercises from API")
    
    for i, exercise in enumerate(exercises[:3]):  # Show first 3
        print(f"{i+1}. {exercise['name']} - Muscle groups: {exercise.get('muscle_groups', 'N/A')}")
    
    return True

if __name__ == "__main__":
    success = test_exercises_api()
    if success:
        print("\n✅ API test successful!")
    else:
        print("\n❌ API test failed!")
