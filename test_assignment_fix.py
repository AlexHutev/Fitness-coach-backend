#!/usr/bin/env python3
"""
Test script to isolate and fix assignment issues
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def login_as_trainer():
    """Login as trainer and get auth token"""
    login_data = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Login successful. Token: {token[:20]}...")
        return token
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_get_assignments(token):
    """Test getting assignments"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nTesting GET /api/v1/assignments")
    response = requests.get(f"{BASE_URL}/api/v1/assignments", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        assignments = response.json()
        print(f"Success! Found {len(assignments)} assignments")
        for i, assignment in enumerate(assignments[:3]):  # Show first 3
            print(f"  {i+1}. Assignment {assignment['id']}: Program {assignment.get('program_name', 'N/A')} -> Client {assignment.get('client_name', 'N/A')}")
        return assignments
    else:
        print(f"Failed: {response.text}")
        return None

def test_assign_program(token):
    """Test assigning a program to clients"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # First, cancel any existing assignments to clear the way
    print("\nClearing existing assignments...")
    assignments = test_get_assignments(token)
    if assignments:
        for assignment in assignments:
            if assignment.get('status') == 'active':
                cancel_url = f"{BASE_URL}/api/v1/assignments/{assignment['id']}"
                cancel_response = requests.delete(cancel_url, headers=headers)
                print(f"  Cancelled assignment {assignment['id']}: {cancel_response.status_code}")
    
    # Now try to assign program 1 to client 1
    print("\nTesting POST /api/v1/programs/1/assign")
    assignment_data = {
        "client_ids": [1],
        "start_date": datetime.now().isoformat(),
        "custom_notes": "Test assignment via API"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/programs/1/assign",
        headers=headers,
        json=assignment_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        assignments = response.json()
        print(f"Success! Created {len(assignments)} assignments")
        for assignment in assignments:
            print(f"  Assignment ID: {assignment.get('id', 'N/A')}")
        return assignments
    else:
        print(f"Failed: {response.text}")
        return None

def get_programs_and_clients(token):
    """Get available programs and clients for testing"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nGetting available programs and clients...")
    
    # Get programs
    programs_response = requests.get(f"{BASE_URL}/api/v1/programs", headers=headers)
    if programs_response.status_code == 200:
        programs = programs_response.json()
        print(f"Programs ({len(programs)}):")
        for program in programs[:3]:
            print(f"  - ID {program['id']}: {program['name']}")
    
    # Get clients
    clients_response = requests.get(f"{BASE_URL}/api/v1/clients", headers=headers)
    if clients_response.status_code == 200:
        clients = clients_response.json()
        print(f"Clients ({len(clients)}):")
        for client in clients[:3]:
            print(f"  - ID {client['id']}: {client['first_name']} {client['last_name']}")

def main():
    print("Testing Assignment API...")
    
    # Step 1: Login
    token = login_as_trainer()
    if not token:
        return
    
    # Step 2: Get current data
    get_programs_and_clients(token)
    
    # Step 3: Test getting assignments
    assignments = test_get_assignments(token)
    
    # Step 4: Test creating new assignment
    new_assignments = test_assign_program(token)
    
    # Step 5: Test getting assignments again
    print("\nTesting GET assignments after assignment...")
    final_assignments = test_get_assignments(token)
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
