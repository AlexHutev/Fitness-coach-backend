#!/usr/bin/env python3
"""
Test script to verify program creation
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_program_creation():
    """Test program creation with trainer credentials"""
    
    # Step 1: Login to get token
    print("1. Logging in with trainer credentials...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    })
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.status_code} - {login_response.text}")
        return False
    
    token_data = login_response.json()
    access_token = token_data.get("access_token")
    print(f"✓ Login successful! Got token: {access_token[:20]}...")
    
    # Step 2: Get user info to verify role
    print("\n2. Getting user info...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if user_response.status_code != 200:
        print(f"✗ Failed to get user info: {user_response.status_code} - {user_response.text}")
        return False
    
    user_data = user_response.json()
    print(f"✓ User info retrieved:")
    print(f"   Email: {user_data.get('email')}")
    print(f"   Role: {user_data.get('role')}")
    print(f"   Active: {user_data.get('is_active')}")
    
    # Step 3: Try to create a program
    print("\n3. Attempting to create a program...")
    program_data = {
        "name": "Test Program",
        "description": "A test program to verify authentication",
        "program_type": "strength",
        "difficulty_level": "beginner",
        "duration_weeks": 4,
        "workout_structure": []
    }
    
    program_response = requests.post(f"{BASE_URL}/programs/", 
                                   json=program_data, 
                                   headers=headers)
    
    print(f"Response status: {program_response.status_code}")
    print(f"Response body: {program_response.text}")
    
    if program_response.status_code == 201:
        print("✓ Program created successfully!")
        program_result = program_response.json()
        print(f"   Program ID: {program_result.get('id')}")
        print(f"   Program Name: {program_result.get('name')}")
        return True
    elif program_response.status_code == 403:
        print("✗ Authorization failed! Still getting 403 error.")
        print("This means the role check is still not working properly.")
        return False
    else:
        print(f"✗ Unexpected error: {program_response.status_code}")
        return False

if __name__ == "__main__":
    print("=== Testing Program Creation with Trainer Role ===\n")
    success = test_program_creation()
    
    if success:
        print("\nAll tests passed! The role authentication is working correctly.")
    else:
        print("\nTests failed! The role authentication needs further investigation.")
