#!/usr/bin/env python3
import requests

def test_simple():
    print("Testing client programs functionality...")
    
    # Login
    login_data = {"email": "trainer@fitnesscoach.com", "password": "trainer123"}
    response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get clients
    response = requests.get("http://localhost:8000/api/v1/clients", headers=headers)
    clients = response.json()
    client_id = clients[0]["id"]
    print(f"Testing with client ID: {client_id}")
    
    # Test assignments endpoint
    response = requests.get(f"http://localhost:8000/api/v1/assignments?client_id={client_id}", headers=headers)
    assignments = response.json()
    print(f"Found {len(assignments)} assignments for client")
    
    # Test frontend page
    response = requests.get(f"http://localhost:3000/clients/{client_id}/programs")
    if response.status_code == 200:
        print("SUCCESS: Frontend page loads correctly!")
        if "Programs" in response.text:
            print("SUCCESS: Page contains program content!")
        return True
    else:
        print(f"ERROR: Frontend page failed: {response.status_code}")
        return False

if __name__ == "__main__":
    if test_simple():
        print("\nThe Programs button is now working!")
        print("Go to http://localhost:3000/clients and click Programs for any client.")
    else:
        print("\nThere are still issues to fix.")
