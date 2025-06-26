#!/usr/bin/env python3

import requests
import json

def test_dashboard_stats_only():
    base_url = "http://localhost:8000/api/v1"
    
    print("Testing Dashboard Stats API...")
    
    # Login first
    client_login = {
        "email": "iveta@gmail.com",
        "password": "iveta123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=client_login)
    if response.status_code == 200:
        client_token = response.json()['access_token']
        client_headers = {"Authorization": f"Bearer {client_token}"}
        
        # Test dashboard stats specifically
        stats_response = requests.get(f"{base_url}/client-dashboard/dashboard-stats", headers=client_headers)
        print(f"Stats API status: {stats_response.status_code}")
        print(f"Stats API response: {stats_response.text}")
        
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    test_dashboard_stats_only()
