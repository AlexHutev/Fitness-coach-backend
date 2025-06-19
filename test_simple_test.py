import requests

# Test the test endpoint
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
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        
        # Test the test endpoint
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        test_response = requests.get(
            "http://localhost:8000/api/v1/schedule/test",
            headers=auth_headers
        )
        
        print(f"Test endpoint response: {test_response.status_code}")
        if test_response.status_code == 200:
            print(f"Success: {test_response.json()}")
        else:
            print(f"Error: {test_response.text}")
    else:
        print(f"Login failed: {login_response.text}")
        
except Exception as e:
    print(f"Error: {e}")
