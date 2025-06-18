#!/usr/bin/env python3
import requests

def test_api():
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # Login
    print("\nLogging in...")
    login_data = {"email": "trainer@fitnesscoach.com", "password": "trainer123"}
    try:
        response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("Login successful!")
        else:
            print(f"Login failed: {response.text}")
            return
    except Exception as e:
        print(f"Login error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test assignments endpoint
    print("\nTesting assignments endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/assignments", headers=headers)
        print(f"Assignments: {response.status_code}")
        if response.status_code == 200:
            assignments = response.json()
            print(f"Found {len(assignments)} assignments")
            for assignment in assignments[:2]:  # Show first 2
                print(f"  - {assignment.get('program_name')} -> {assignment.get('client_name')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Assignments error: {e}")

if __name__ == "__main__":
    test_api()
