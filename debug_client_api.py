#!/usr/bin/env python3

import requests
import json

def debug_client_api():
    base_url = "http://localhost:8000/api/v1"
    
    print("=== DEBUGGING CLIENT API ===")
    
    # Test client login
    print("1. Testing Client Login...")
    client_login = {
        "email": "iveta@gmail.com",
        "password": "iveta123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=client_login)
    if response.status_code == 200:
        client_token = response.json()['access_token']
        client_headers = {"Authorization": f"Bearer {client_token}"}
        print("SUCCESS: Client login successful")
        
        # Test client profile
        print("\n2. Testing Client Profile...")
        profile_response = requests.get(f"{base_url}/client-dashboard/profile", headers=client_headers)
        print(f"Profile API status: {profile_response.status_code}")
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("Profile data structure:")
            print(json.dumps(profile_data, indent=2))
        else:
            print(f"Profile error: {profile_response.text}")
            
        # Test client programs
        print("\n3. Testing Client Programs...")
        programs_response = requests.get(f"{base_url}/client-dashboard/programs", headers=client_headers)
        print(f"Programs API status: {programs_response.status_code}")
        if programs_response.status_code == 200:
            programs_data = programs_response.json()
            print("Programs data structure:")
            print(json.dumps(programs_data, indent=2))
        else:
            print(f"Programs error: {programs_response.text}")
            
        # Test client dashboard stats
        print("\n4. Testing Client Dashboard Stats...")
        stats_response = requests.get(f"{base_url}/client-dashboard/dashboard-stats", headers=client_headers)
        print(f"Stats API status: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print("Stats data structure:")
            print(json.dumps(stats_data, indent=2))
        else:
            print(f"Stats error: {stats_response.text}")
            
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    debug_client_api()
