#!/usr/bin/env python3

import requests
import json

def test_client_login():
    base_url = "http://localhost:8000/api/v1"
    
    print("Testing Client Login...")
    client_login = {
        "email": "iveta@gmail.com",
        "password": "iveta123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=client_login)
    print(f"Client login status: {response.status_code}")
    
    if response.status_code == 200:
        client_data = response.json()
        client_token = client_data['access_token']
        client_headers = {"Authorization": f"Bearer {client_token}"}
        
        print("SUCCESS: Client login successful!")
        print(f"Token: {client_token[:20]}...")
        
        # Test client dashboard
        profile_response = requests.get(f"{base_url}/client-dashboard/profile", headers=client_headers)
        print(f"Client profile API status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"Client: {profile['user_info']['first_name']} {profile['user_info']['last_name']}")
            print(f"Trainer: {profile['trainer_info']['name']}")
            return True
        else:
            print(f"Profile API failed: {profile_response.text}")
            return False
    else:
        print(f"Login failed: {response.text}")
        return False

if __name__ == "__main__":
    success = test_client_login()
    if success:
        print("\nClient login is now working!")
    else:
        print("\nClient login still has issues.")
