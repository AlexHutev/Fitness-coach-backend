#!/usr/bin/env python3

import requests
import json

def test_api():
    base_url = "http://localhost:8000/api/v1"
    
    # Test trainer login
    print("=== Testing Trainer Login ===")
    trainer_login = {
        "email": "trainer@fitnesscoach.com",
        "password": "trainer123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=trainer_login)
    print(f"Trainer login status: {response.status_code}")
    
    if response.status_code == 200:
        trainer_data = response.json()
        trainer_token = trainer_data['access_token']
        trainer_headers = {"Authorization": f"Bearer {trainer_token}"}
        
        # Test getting trainer's clients
        print("\n=== Testing Trainer's Clients ===")
        clients_response = requests.get(f"{base_url}/clients/", headers=trainer_headers)
        print(f"Clients API status: {clients_response.status_code}")
        if clients_response.status_code == 200:
            clients = clients_response.json()
            print(f"Number of clients: {len(clients)}")
            for client in clients:
                print(f"  Client: {client['first_name']} {client['last_name']} (ID: {client['id']})")
        
        # Test getting trainer's programs
        print("\n=== Testing Trainer's Programs ===")
        programs_response = requests.get(f"{base_url}/programs/", headers=trainer_headers)
        print(f"Programs API status: {programs_response.status_code}")
        if programs_response.status_code == 200:
            programs = programs_response.json()
            print(f"Number of programs: {len(programs)}")
            for program in programs:
                print(f"  Program: {program['name']} (ID: {program['id']})")
        
        # Test getting assignments
        print("\n=== Testing Program Assignments ===")
        assignments_response = requests.get(f"{base_url}/assignments/", headers=trainer_headers)
        print(f"Assignments API status: {assignments_response.status_code}")
        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            print(f"Number of assignments: {len(assignments)}")
            for assignment in assignments:
                print(f"  Assignment: {assignment['program_name']} -> {assignment['client_name']}")
    
    # Test client login
    print("\n=== Testing Client Login ===")
    client_login = {
        "email": "iveta@gmail.com", 
        "password": "iveta123"
    }
    
    response = requests.post(f"{base_url}/auth/login", json=client_login)
    print(f"Client login status: {response.status_code}")
    
    if response.status_code == 200:
        client_data = response.json()
        client_token = client_data['access_token']
        client_headers = {"Authorization": f"Bearer {client_token}"}
        
        # Test client dashboard profile
        print("\n=== Testing Client Dashboard ===")
        profile_response = requests.get(f"{base_url}/client-dashboard/profile", headers=client_headers)
        print(f"Client profile API status: {profile_response.status_code}")
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"Client: {profile['user_info']['first_name']} {profile['user_info']['last_name']}")
            print(f"Trainer: {profile['trainer_info']['name']}")
        
        # Test client programs
        print("\n=== Testing Client Programs ===")
        client_programs_response = requests.get(f"{base_url}/client-dashboard/programs", headers=client_headers)
        print(f"Client programs API status: {client_programs_response.status_code}")
        if client_programs_response.status_code == 200:
            client_programs = client_programs_response.json()
            print(f"Number of assigned programs: {len(client_programs['assigned_programs'])}")
            for program in client_programs['assigned_programs']:
                print(f"  Program: {program['program_name']} (Status: {program['status']})")
        
        # Test weekly exercises
        print("\n=== Testing Client Weekly Exercises ===")
        client_id = 1  # Iveta's client ID
        weekly_response = requests.get(f"{base_url}/weekly-exercises/client/{client_id}/current-week", headers=client_headers)
        print(f"Weekly exercises API status: {weekly_response.status_code}")
        if weekly_response.status_code == 200:
            weekly_exercises = weekly_response.json()
            print(f"Number of current week exercises: {len(weekly_exercises)}")
            for exercise in weekly_exercises[:5]:  # Show first 5
                print(f"  Exercise: {exercise['exercise_name']} - Day {exercise['day_number']} (Status: {exercise['status']})")

if __name__ == "__main__":
    test_api()
