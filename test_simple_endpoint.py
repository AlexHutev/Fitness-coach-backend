import requests
import json

def test_simple_endpoint():
    """Test a simple endpoint that should work"""
    
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
        
        # Test a simple endpoint that should work (clients)
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        clients_response = requests.get(
            "http://localhost:8000/api/v1/clients/",
            headers=auth_headers
        )
        
        print(f"Clients response: {clients_response.status_code}")
        if clients_response.status_code == 200:
            print("Clients endpoint works!")
        else:
            print(f"Clients error: {clients_response.text}")
        
        # Test basic appointments endpoint without today_only
        appointments_response = requests.get(
            "http://localhost:8000/api/v1/appointments",
            headers=auth_headers
        )
        
        print(f"Basic appointments response: {appointments_response.status_code}")
        if appointments_response.status_code == 200:
            print("Basic appointments endpoint works!")
        else:
            print(f"Basic appointments error: {appointments_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_endpoint()
