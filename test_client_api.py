"""
Test the client login API directly
"""

import requests
import json

def test_client_login():
    """Test client login endpoint"""
    
    url = "http://localhost:8000/api/v1/client/login"
    
    # Test credentials we created
    data = {
        "email": "john@client.com",
        "password": "client123"
    }
    
    try:
        print("Testing client login API...")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = requests.post(url, json=data)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Login successful!")
            print(f"Access Token: {result.get('access_token', 'N/A')[:20]}...")
            print(f"Client ID: {result.get('client_id')}")
            print(f"Assignment ID: {result.get('assignment_id')}")
            print(f"Program Name: {result.get('program_name')}")
            
            # Test dashboard endpoint
            print("\n" + "="*50)
            print("Testing dashboard endpoint...")
            
            headers = {
                "Authorization": f"Bearer {result['access_token']}"
            }
            
            dashboard_response = requests.get(
                "http://localhost:8000/api/v1/client/dashboard", 
                headers=headers
            )
            
            print(f"Dashboard Status: {dashboard_response.status_code}")
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                print(f"[OK] Dashboard loaded!")
                print(f"Client Name: {dashboard_data.get('client_name')}")
                print(f"Active Programs: {len(dashboard_data.get('active_programs', []))}")
                print(f"Recent Workouts: {len(dashboard_data.get('recent_workouts', []))}")
            else:
                print(f"[ERROR] Dashboard failed: {dashboard_response.text}")
                
        else:
            print(f"[ERROR] Login failed: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    test_client_login()