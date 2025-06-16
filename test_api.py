#!/usr/bin/env python3
"""
Simple script to test the API authentication and exercise creation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login and get token"""
    login_data = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Token received: {token[:20]}...")
        return token
    else:
        print(f"Login failed: {response.text}")
        return None

def test_create_exercise(token):
    """Test creating an exercise"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    exercise_data = {
        "name": "Test Exercise",
        "description": "Test description",
        "difficulty_level": "beginner",
        "muscle_groups": ["chest"],
        "equipment": ["bodyweight"],
        "is_public": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/exercises/", 
                           json=exercise_data, 
                           headers=headers)
    
    print(f"Create Exercise Status: {response.status_code}")
    if response.status_code == 201:
        print("Exercise created successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Creation failed: {response.text}")

def main():
    """Main test function"""
    print("Testing FitnessCoach API...")
    
    # Test login
    token = test_login()
    if not token:
        return
    
    # Test exercise creation
    test_create_exercise(token)

if __name__ == "__main__":
    main()
