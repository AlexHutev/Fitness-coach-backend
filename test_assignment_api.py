#!/usr/bin/env python3
"""
Test the assignment functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_assignment_api():
    print("Testing Assignment API...")
    
    # Login first
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Login successful. Token: {token[:20]}...")
    
    # Test GET /api/v1/assignments - should return empty list now
    print("\nTesting GET /api/v1/assignments")
    response = requests.get(f"{BASE_URL}/api/v1/assignments", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        assignments = response.json()
        print(f"Found {len(assignments)} assignments")
    else:
        print(f"Failed: {response.text}")
    
    # Get available programs and clients for assignment
    print("\nGetting available programs and clients...")
    programs_response = requests.get(f"{BASE_URL}/api/v1/programs?is_template=true", headers=headers)
    clients_response = requests.get(f"{BASE_URL}/api/v1/clients", headers=headers)
    
    if programs_response.status_code == 200 and clients_response.status_code == 200:
        programs = programs_response.json()
        clients = clients_response.json()
        
        print(f"Programs ({len(programs)}):")
        for p in programs[:3]:  # Show first 3
            print(f"  - ID {p['id']}: {p['name']}")
        
        print(f"Clients ({len(clients)}):")
        for c in clients[:3]:  # Show first 3
            print(f"  - ID {c['id']}: {c['first_name']} {c['last_name']}")
        
        if programs and clients:
            # Test assignment creation
            program_id = programs[0]['id']
            client_id = clients[0]['id']
            
            print(f"\nTesting POST /api/v1/programs/{program_id}/assign")
            assignment_data = {
                "client_ids": [client_id],
                "start_date": "2025-06-19T00:00:00",
                "custom_notes": "Test assignment via API"
            }
            
            assign_response = requests.post(
                f"{BASE_URL}/api/v1/programs/{program_id}/assign",
                headers=headers,
                json=assignment_data
            )
            
            print(f"Status: {assign_response.status_code}")
            if assign_response.status_code == 200:
                assignments = assign_response.json()
                print(f"Successfully created {len(assignments)} assignment(s)")
                for assignment in assignments:
                    print(f"  - Assignment ID: {assignment['id']}")
            else:
                print(f"Failed: {assign_response.text}")
            
            # Test getting assignments again
            print("\nTesting GET assignments after assignment...")
            response = requests.get(f"{BASE_URL}/api/v1/assignments", headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                assignments = response.json()
                print(f"Found {len(assignments)} assignments")
                for assignment in assignments:
                    print(f"  - {assignment['client_name']} -> {assignment['program_name']} (Status: {assignment['status']})")
            else:
                print(f"Failed: {response.text}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_assignment_api()
