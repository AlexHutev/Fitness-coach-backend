#!/usr/bin/env python3
"""
Test the program assignment functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def login_as_trainer():
    """Login as trainer and get token"""
    login_data = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[SUCCESS] Logged in successfully")
        return token
    else:
        print(f"[ERROR] Login failed: {response.text}")
        return None

def get_headers(token):
    """Get headers with authorization"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def test_program_endpoints(token):
    """Test program-related endpoints"""
    headers = get_headers(token)
    
    # Get programs
    print("\n[INFO] Testing GET /api/v1/programs")
    response = requests.get(f"{BASE_URL}/api/v1/programs", headers=headers)
    if response.status_code == 200:
        programs = response.json()
        print(f"[SUCCESS] Found {len(programs)} programs")
        return programs
    else:
        print(f"[ERROR] Failed to get programs: {response.text}")
        return []

def test_clients_endpoints(token):
    """Test client-related endpoints"""
    headers = get_headers(token)
    
    # Get clients
    print("\n[INFO] Testing GET /api/v1/clients")
    response = requests.get(f"{BASE_URL}/api/v1/clients", headers=headers)
    if response.status_code == 200:
        clients = response.json()
        print(f"[SUCCESS] Found {len(clients)} clients")
        return clients
    else:
        print(f"[ERROR] Failed to get clients: {response.text}")
        return []

def test_assignment_endpoints(token, programs, clients):
    """Test assignment endpoints"""
    headers = get_headers(token)
    
    if not programs or not clients:
        print("[ERROR] No programs or clients available for testing assignments")
        return
    
    program_id = programs[0]["id"]
    client_id = clients[0]["id"]
    
    print(f"\n[INFO] Testing program assignment: Program {program_id} to Client {client_id}")
    
    # Test assignment
    assignment_data = {
        "client_ids": [client_id],
        "start_date": "2025-06-20",
        "custom_notes": "Test assignment from API"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/programs/{program_id}/assign",
        headers=headers,
        json=assignment_data
    )
    
    if response.status_code == 200:
        assignments = response.json()
        print(f"[SUCCESS] Assignment created successfully")
        print(f"   Assignment ID: {assignments[0]['id']}")
        return assignments[0]["id"]
    else:
        print(f"[ERROR] Assignment failed: {response.text}")
        return None

def test_get_assignments(token):
    """Test getting assignments"""
    headers = get_headers(token)
    
    print("\n[INFO] Testing GET /api/v1/assignments")
    response = requests.get(f"{BASE_URL}/api/v1/assignments", headers=headers)
    
    if response.status_code == 200:
        assignments = response.json()
        print(f"[SUCCESS] Found {len(assignments)} assignments")
        for assignment in assignments:
            print(f"   - Assignment {assignment['id']}: {assignment.get('program_name', 'Unknown')} -> {assignment.get('client_name', 'Unknown')}")
        return assignments
    else:
        print(f"[ERROR] Failed to get assignments: {response.text}")
        return []

def main():
    """Main test function"""
    print("Testing Program Assignment Functionality")
    print("=" * 50)
    
    # Login
    token = login_as_trainer()
    if not token:
        return
    
    # Test programs
    programs = test_program_endpoints(token)
    
    # Test clients
    clients = test_clients_endpoints(token)
    
    # Test assignments
    assignment_id = test_assignment_endpoints(token, programs, clients)
    
    # Get all assignments
    assignments = test_get_assignments(token)
    
    print("\n" + "=" * 50)
    print("Testing completed!")

if __name__ == "__main__":
    main()
