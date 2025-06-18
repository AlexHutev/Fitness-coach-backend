#!/usr/bin/env python3
"""
Simple test for assignment functionality
"""
import requests
import json

def test_assignments():
    # Login
    login_data = {"email": "trainer@fitnesscoach.com", "password": "trainer123"}
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Login successful")
    
    # Test GET assignments
    response = requests.get("http://localhost:8000/api/v1/assignments", headers=headers)
    print(f"GET /assignments: {response.status_code}")
    if response.status_code == 200:
        assignments = response.json()
        print(f"Found {len(assignments)} assignments")
    else:
        print(f"Error: {response.text}")
    
    # Get programs and clients
    programs_response = requests.get("http://localhost:8000/api/v1/programs", headers=headers)
    clients_response = requests.get("http://localhost:8000/api/v1/clients", headers=headers)
    
    if programs_response.status_code == 200 and clients_response.status_code == 200:
        programs = programs_response.json()
        clients = clients_response.json()
        
        print(f"Found {len(programs)} programs, {len(clients)} clients")
        
        if programs and clients:
            # Test program assignment
            assign_data = {
                "client_ids": [clients[0]["id"]],
                "start_date": "2025-06-19T10:00:00",
                "custom_notes": "Test assignment"
            }
            
            assign_response = requests.post(
                f"http://localhost:8000/api/v1/programs/{programs[0]['id']}/assign",
                headers=headers,
                json=assign_data
            )
            
            print(f"POST /programs/{programs[0]['id']}/assign: {assign_response.status_code}")
            if assign_response.status_code == 200:
                result = assign_response.json()
                print(f"Created {len(result)} assignment(s)")
                
                # Test GET assignments again
                response = requests.get("http://localhost:8000/api/v1/assignments", headers=headers)
                if response.status_code == 200:
                    assignments = response.json()
                    print(f"Now have {len(assignments)} assignments")
                    for assignment in assignments:
                        print(f"  - {assignment['client_name']} -> {assignment['program_name']}")
            else:
                print(f"Assignment failed: {assign_response.text}")
    
if __name__ == "__main__":
    test_assignments()
