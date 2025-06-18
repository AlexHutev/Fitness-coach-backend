import requests
import json

# Test client login
url = "http://localhost:8000/api/v1/client/login"
data = {"email": "john@client.com", "password": "client123"}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS!")
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"Client ID: {result.get('client_id')}")
        print(f"Assignment ID: {result.get('assignment_id')}")
    else:
        print("FAILED!")
        
except Exception as e:
    print(f"Error: {e}")
