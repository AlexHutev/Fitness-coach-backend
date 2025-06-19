import requests
import json

def test_simple_appointments():
    """Test the simple appointments endpoint"""
    
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
        print(f"Login successful")
        
        # Test the simple appointments endpoint
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        test_response = requests.get(
            "http://localhost:8000/api/v1/appointments/test",
            headers=auth_headers
        )
        
        print(f"Simple test response: {test_response.status_code}")
        if test_response.status_code == 200:
            print(f"Success: {test_response.json()}")
        else:
            print(f"Error: {test_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_appointments()
