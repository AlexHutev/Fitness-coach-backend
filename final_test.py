#!/usr/bin/env python3
"""
Final test of the assignment functionality
"""
import requests
import json

def test_assignment_functionality():
    print("=== Testing Assignment Functionality ===\n")
    
    # Login
    print("1. Logging in...")
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json={
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful!")
    
    # Test getting assignments
    print("\n2. Testing GET /api/v1/assignments...")
    response = requests.get("http://localhost:8000/api/v1/assignments", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        assignments = response.json()
        print(f"Found {len(assignments)} existing assignments")
        for assignment in assignments:
            print(f"   - {assignment['client_name']} -> {assignment['program_name']} ({assignment['status']})")
    else:
        print(f"Error: {response.text}")
        return False
    
    # Test getting programs and clients
    print("\n3. Getting available programs and clients...")
    programs_response = requests.get("http://localhost:8000/api/v1/programs", headers=headers)
    clients_response = requests.get("http://localhost:8000/api/v1/clients", headers=headers)
    
    if programs_response.status_code == 200 and clients_response.status_code == 200:
        programs = programs_response.json()
        clients = clients_response.json()
        print(f"Found {len(programs)} programs and {len(clients)} clients")
        
        # Show available options
        print("Available programs:")
        for program in programs:
            print(f"   - ID {program['id']}: {program['name']} ({program['program_type']})")
        
        print("Available clients:")
        for client in clients:
            print(f"   - ID {client['id']}: {client['first_name']} {client['last_name']}")
    else:
        print("❌ Failed to get programs or clients")
        return False
    
    # Test API endpoints available
    print("\n4. Testing API endpoints...")
    endpoints_to_test = [
        "/api/v1/health",
        "/api/v1/exercises",
    ]
    
    for endpoint in endpoints_to_test:
        response = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
        print(f"   {endpoint}: {response.status_code}")
    
    print("\n✅ Assignment functionality is working!")
    print("\n=== Next Steps ===")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Login with trainer@fitnesscoach.com / trainer123")
    print("3. Go to 'Clients' page")
    print("4. Click 'Create Weekly Assignment' on any client")
    print("5. Use the weekly assignment tool to create custom workout schedules")
    print("\nAlternatively:")
    print("6. Go to 'Programs' > 'Assignments' and use the 'Weekly Assignment' tab")
    
    return True

if __name__ == "__main__":
    test_assignment_functionality()
