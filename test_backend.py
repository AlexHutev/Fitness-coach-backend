import requests
import json

def test_backend_connection():
    """Test if the backend is responding properly"""
    
    try:
        # Test basic health check
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"Health check: {response.status_code}")
        
        if response.status_code == 200:
            print("Backend is running!")
        else:
            print("Backend health check failed")
            
    except Exception as e:
        print(f"Error connecting to backend: {e}")

def test_login():
    """Test login to get a token"""
    
    try:
        login_data = {
            "email": "trainer@fitnesscoach.com",
            "password": "trainer123"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json=login_data,  # Use JSON format
            headers=headers
        )
        
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Login successful!")
            token = data.get("access_token")
            print(f"Token: {token[:20]}...")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def test_appointments_endpoint(token):
    """Test the appointments/today endpoint"""
    
    if not token:
        print("No token available for testing")
        return
        
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test the exact URL being used
        url = "http://localhost:8000/api/v1/appointments?today_only=true"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Appointments today response: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('appointments', [])
            print(f"Found {len(appointments)} appointments today")
            for apt in appointments:
                print(f"  - {apt.get('title', 'No title')} at {apt.get('start_time', 'No time')}")
        else:
            print(f"Appointments request failed: {response.text}")
            
    except Exception as e:
        print(f"Error fetching appointments: {e}")

if __name__ == "__main__":
    print("Testing Backend Connection...\n")
    
    # Test 1: Health check
    test_backend_connection()
    print()
    
    # Test 2: Login
    token = test_login()
    print()
    
    # Test 3: Appointments
    test_appointments_endpoint(token)
