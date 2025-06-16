#!/usr/bin/env python3
"""
Test the complete login flow like the frontend does
"""

import requests
import json

def test_login_flow():
    """Test the complete login flow"""
    base_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    print("Testing Login Flow")
    print("=" * 50)
    
    # Step 1: Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Step 2: Test CORS preflight
    print("\n2. Testing CORS preflight...")
    try:
        headers = {
            "Origin": frontend_url,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        response = requests.options(f"{base_url}/api/v1/auth/login", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Step 3: Test login
    print("\n3. Testing login...")
    try:
        headers = {
            "Content-Type": "application/json",
            "Origin": frontend_url
        }
        
        login_data = {
            "email": "trainer@fitnesscoach.com",
            "password": "trainer123"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            headers=headers,
            json=login_data
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Login successful!")
            print(f"   Access token: {data['access_token'][:50]}...")
            
            # Step 4: Test authenticated endpoint
            print("\n4. Testing authenticated endpoint...")
            auth_headers = {
                "Authorization": f"Bearer {data['access_token']}",
                "Origin": frontend_url
            }
            
            me_response = requests.get(f"{base_url}/api/v1/auth/me", headers=auth_headers)
            print(f"   Status: {me_response.status_code}")
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print(f"   User data retrieved!")
                print(f"   User: {user_data['first_name']} {user_data['last_name']}")
                print(f"   Email: {user_data['email']}")
                print(f"   Role: {user_data['role']}")
            else:
                print(f"   Error: {me_response.text}")
                
        else:
            print(f"   Login failed: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_login_flow()