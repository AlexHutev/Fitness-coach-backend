import sys
sys.path.append('.')

import requests
import json

def test_endpoint_with_auth():
    """Test the endpoint with proper authentication"""
    
    try:
        # Login first
        login_data = {
            "email": "trainer@fitnesscoach.com",
            "password": "trainer123"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        login_response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,
            headers=headers
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
            
        token = login_response.json().get("access_token")
        print(f"Login successful, token: {token[:20]}...")
        
        # Now test the appointments endpoint
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        appointments_response = requests.get(
            "http://localhost:8000/api/v1/appointments?today_only=true",
            headers=auth_headers
        )
        
        print(f"Appointments response: {appointments_response.status_code}")
        print(f"Response content: {appointments_response.text}")
        
        if appointments_response.status_code == 200:
            data = appointments_response.json()
            print(f"Success! Found {data.get('total', 0)} appointments")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint_with_auth()
