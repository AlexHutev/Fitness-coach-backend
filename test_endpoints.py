import requests

# Test different endpoints to see what's available
try:
    # Test health endpoint first
    health_response = requests.get("http://localhost:8000/api/v1/health")
    print(f"Health: {health_response.status_code}")
    
    # Test schedule endpoint without auth
    schedule_response = requests.get("http://localhost:8000/api/v1/schedule/")
    print(f"Schedule (no auth): {schedule_response.status_code}")
    
    # Test with login
    login_data = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test schedule with auth
        schedule_auth_response = requests.get(
            "http://localhost:8000/api/v1/schedule/",
            headers=auth_headers
        )
        print(f"Schedule (with auth): {schedule_auth_response.status_code}")
        if schedule_auth_response.status_code == 200:
            print(f"Success: {schedule_auth_response.json()}")
        else:
            print(f"Error: {schedule_auth_response.text}")
        
        # Test the schedule today endpoint
        schedule_today_response = requests.get(
            "http://localhost:8000/api/v1/schedule/?today_only=true",
            headers=auth_headers
        )
        print(f"Schedule today: {schedule_today_response.status_code}")
        if schedule_today_response.status_code == 200:
            print(f"Success: {schedule_today_response.json()}")
        else:
            print(f"Error: {schedule_today_response.text}")
    
except Exception as e:
    print(f"Error: {e}")
