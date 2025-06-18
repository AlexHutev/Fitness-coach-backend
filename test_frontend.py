#!/usr/bin/env python3
import requests

def test_frontend():
    try:
        # Test the main frontend page
        print("Testing frontend health...")
        response = requests.get("http://localhost:3000")
        print(f"Frontend root: {response.status_code}")
        
        # Test the specific client programs page
        print("\nTesting client programs page...")
        response = requests.get("http://localhost:3000/clients/1/programs")
        print(f"Client programs page: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Page loaded successfully!")
            if "Programs" in response.text:
                print("SUCCESS: Page contains 'Programs' text")
        else:
            print(f"ERROR: Page failed to load: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"ERROR: Error testing frontend: {e}")

if __name__ == "__main__":
    test_frontend()
