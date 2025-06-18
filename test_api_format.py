#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_api_response_format():
    """Test the exact API response format that the frontend expects"""
    
    # Login first
    login_data = {"email": "trainer@fitnesscoach.com", "password": "trainer123"}
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return False
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test exercises endpoint with correct limit parameter
    exercises_response = requests.get("http://localhost:8000/api/v1/exercises/?limit=100", headers=headers)
    
    print(f"Status Code: {exercises_response.status_code}")
    print(f"Response Headers: {dict(exercises_response.headers)}")
    
    if exercises_response.status_code == 200:
        exercises_data = exercises_response.json()
        print(f"Response Type: {type(exercises_data)}")
        print(f"Number of exercises: {len(exercises_data) if isinstance(exercises_data, list) else 'Not a list'}")
        
        if isinstance(exercises_data, list) and len(exercises_data) > 0:
            print(f"First exercise structure:")
            print(json.dumps(exercises_data[0], indent=2))
            
            # Check muscle_groups format
            first_ex = exercises_data[0]
            if 'muscle_groups' in first_ex:
                print(f"muscle_groups type: {type(first_ex['muscle_groups'])}")
                print(f"muscle_groups value: {first_ex['muscle_groups']}")
        
        return True
    else:
        print(f"API Error: {exercises_response.text}")
        return False

if __name__ == "__main__":
    test_api_response_format()
