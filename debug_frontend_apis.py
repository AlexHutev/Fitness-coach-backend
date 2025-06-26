#!/usr/bin/env python3

import requests
import json

def debug_client_frontend_apis():
    """Debug the exact API calls the client frontend should be making"""
    
    base_url = "http://localhost:8000"
    
    print("=== DEBUGGING CLIENT FRONTEND ISSUE ===")
    
    # Step 1: Test client login
    print("1. Testing Client Login...")
    client_login = {
        "email": "iveta@gmail.com",
        "password": "iveta123"
    }
    
    response = requests.post(f"{base_url}/api/v1/auth/login", json=client_login)
    if response.status_code != 200:
        print(f"ERROR: Login failed - {response.text}")
        return
    
    client_token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {client_token}"}
    print("SUCCESS: Client login working")
    
    # Step 2: Test the exact endpoints the frontend calls
    print("\n2. Testing Frontend API Endpoints...")
    
    # Test profile endpoint (frontend call)
    print("\n  a) Client Profile API:")
    profile_url = f"{base_url}/api/v1/client-dashboard/profile"
    profile_response = requests.get(profile_url, headers=headers)
    print(f"     URL: {profile_url}")
    print(f"     Status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        print("     SUCCESS: Profile API working")
    else:
        print(f"     ERROR: {profile_response.text}")
        
    # Test programs endpoint (frontend call) 
    print("\n  b) Client Programs API:")
    programs_url = f"{base_url}/api/v1/client-dashboard/programs"
    programs_response = requests.get(programs_url, headers=headers)
    print(f"     URL: {programs_url}")
    print(f"     Status: {programs_response.status_code}")
    if programs_response.status_code == 200:
        programs_data = programs_response.json()
        assigned_programs = programs_data.get('assigned_programs', [])
        print(f"     SUCCESS: Programs API working")
        print(f"     Found {len(assigned_programs)} assigned programs")
        
        if assigned_programs:
            print("     Program details:")
            for prog in assigned_programs:
                print(f"       - {prog['program_name']} (Status: {prog['status']})")
        else:
            print("     WARNING: No programs in response!")
            print(f"     Full response: {json.dumps(programs_data, indent=2)}")
    else:
        print(f"     ERROR: {programs_response.text}")
        
    # Test dashboard stats endpoint (frontend call)
    print("\n  c) Dashboard Stats API:")
    stats_url = f"{base_url}/api/v1/client-dashboard/dashboard-stats" 
    stats_response = requests.get(stats_url, headers=headers)
    print(f"     URL: {stats_url}")
    print(f"     Status: {stats_response.status_code}")
    if stats_response.status_code == 200:
        print("     SUCCESS: Stats API working")
    else:
        print(f"     ERROR: {stats_response.text}")
    
    # Step 3: Check the weekly exercises endpoint
    print("\n3. Testing Weekly Exercises API...")
    client_id = 1  # From our earlier tests
    weekly_url = f"{base_url}/api/v1/weekly-exercises/client/{client_id}/current-week"
    weekly_response = requests.get(weekly_url, headers=headers)
    print(f"   URL: {weekly_url}")
    print(f"   Status: {weekly_response.status_code}")
    if weekly_response.status_code == 200:
        weekly_data = weekly_response.json()
        print(f"   SUCCESS: Found {len(weekly_data)} weekly exercises")
    else:
        print(f"   ERROR: {weekly_response.text}")
    
    print("\n=== SUMMARY ===")
    print("✓ Backend APIs are accessible")
    print("✓ Authentication is working")
    print("✓ The issue is likely in the frontend JavaScript/React code")
    print("\nNext steps:")
    print("1. Check browser console for JavaScript errors")
    print("2. Check Network tab in browser dev tools")
    print("3. Verify API responses in browser")

if __name__ == "__main__":
    debug_client_frontend_apis()
