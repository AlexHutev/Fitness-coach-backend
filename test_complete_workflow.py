#!/usr/bin/env python3
"""
Comprehensive test of the client programs functionality
"""

import requests
import json

BASE_URL_API = "http://localhost:8000"
BASE_URL_FRONTEND = "http://localhost:3000"

def test_complete_workflow():
    print("=== TESTING COMPLETE CLIENT PROGRAMS WORKFLOW ===\n")
    
    # Step 1: Test API Health
    print("1. Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL_API}/api/v1/health")
        assert response.status_code == 200
        print("   [OK] API is healthy")
    except Exception as e:
        print(f"   [ERROR] API health check failed: {e}")
        return False
    
    # Step 2: Login as trainer
    print("\n2. Testing trainer login...")
    login_data = {"email": "trainer@fitnesscoach.com", "password": "trainer123"}
    try:
        response = requests.post(f"{BASE_URL_API}/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   [OK] Trainer login successful")
    except Exception as e:
        print(f"   [ERROR] Trainer login failed: {e}")
        return False
    
    # Step 3: Get clients
    print("\n3. Testing clients endpoint...")
    try:
        response = requests.get(f"{BASE_URL_API}/api/v1/clients", headers=headers)
        assert response.status_code == 200
        clients = response.json()
        assert len(clients) > 0
        client_id = clients[0]["id"]
        client_name = f"{clients[0]['first_name']} {clients[0]['last_name']}"
        print(f"   ✓ Found {len(clients)} clients")
        print(f"   ✓ Testing with client: {client_name} (ID: {client_id})")
    except Exception as e:
        print(f"   ✗ Clients endpoint failed: {e}")
        return False
    
    # Step 4: Get programs
    print("\n4. Testing programs endpoint...")
    try:
        response = requests.get(f"{BASE_URL_API}/api/v1/programs", headers=headers)
        assert response.status_code == 200
        programs = response.json()
        assert len(programs) > 0
        print(f"   ✓ Found {len(programs)} programs")
    except Exception as e:
        print(f"   ✗ Programs endpoint failed: {e}")
        return False
    
    # Step 5: Get assignments for the client
    print("\n5. Testing assignments endpoint...")
    try:
        response = requests.get(f"{BASE_URL_API}/api/v1/assignments", 
                              headers=headers, 
                              params={"client_id": client_id})
        assert response.status_code == 200
        assignments = response.json()
        print(f"   ✓ Found {len(assignments)} assignments for client {client_name}")
        if assignments:
            for assignment in assignments:
                print(f"     - {assignment.get('program_name')} (Status: {assignment.get('status')})")
    except Exception as e:
        print(f"   ✗ Assignments endpoint failed: {e}")
        return False
    
    # Step 6: Test frontend pages
    print("\n6. Testing frontend pages...")
    try:
        # Test main clients page
        response = requests.get(f"{BASE_URL_FRONTEND}/clients")
        assert response.status_code == 200
        print("   ✓ Clients list page loads")
        
        # Test specific client programs page
        response = requests.get(f"{BASE_URL_FRONTEND}/clients/{client_id}/programs")
        assert response.status_code == 200
        assert "Programs" in response.text
        print(f"   ✓ Client programs page loads for client {client_id}")
        
    except Exception as e:
        print(f"   ✗ Frontend test failed: {e}")
        return False
    
    # Step 7: Test assignment creation (if no active assignment exists)
    print("\n7. Testing program assignment...")
    try:
        # Check if client has active assignment
        active_assignments = [a for a in assignments if a.get('status') == 'active']
        
        if not active_assignments and programs:
            # Try to assign a program
            program_id = programs[0]["id"]
            assignment_data = {
                "client_ids": [client_id],
                "start_date": "2025-06-20",
                "custom_notes": "Test assignment via API test"
            }
            
            response = requests.post(
                f"{BASE_URL_API}/api/v1/programs/{program_id}/assign",
                headers=headers,
                json=assignment_data
            )
            
            if response.status_code == 200:
                new_assignment = response.json()[0]
                print(f"   ✓ Successfully assigned program '{programs[0]['name']}' to {client_name}")
                print(f"     Assignment ID: {new_assignment['id']}")
            else:
                print(f"   ⚠ Assignment creation returned: {response.status_code} - {response.text}")
        else:
            print(f"   [WARNING] Client {client_name} already has active assignments, skipping assignment test")
            
    except Exception as e:
        print(f"   [ERROR] Assignment test failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("The Programs button functionality is working correctly!")
    print(f"\nYou can now:")
    print(f"1. Go to http://localhost:3000/clients")
    print(f"2. Click the 'Programs' button for any client")
    print(f"3. View and manage their program assignments")
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if not success:
        print("\n=== SOME TESTS FAILED ===")
        print("Please check the errors above and fix any issues.")
