#!/usr/bin/env python3

import sqlite3
from werkzeug.security import check_password_hash

def check_passwords():
    conn = sqlite3.connect('fitness_coach.db')
    cursor = conn.cursor()
    
    print('=== User Password Check ===')
    
    # Get all users
    cursor.execute('SELECT id, email, hashed_password FROM users')
    users = cursor.fetchall()
    
    for user in users:
        print(f'\nUser ID {user[0]}: {user[1]}')
        print(f'Has password hash: {bool(user[2])}')
        if user[2]:
            print(f'Hash length: {len(user[2])} characters')
            
            # Test common passwords
            test_passwords = []
            if 'admin' in user[1]:
                test_passwords = ['admin123', 'password', 'admin']
            elif 'trainer' in user[1]:
                test_passwords = ['trainer123', 'password', 'trainer']
            elif 'iveta' in user[1]:
                test_passwords = ['iveta123', 'password', 'client123', 'iveta']
            
            for pwd in test_passwords:
                try:
                    is_valid = check_password_hash(user[2], pwd)
                    print(f'  Password "{pwd}": {"✓ VALID" if is_valid else "✗ Invalid"}')
                    if is_valid:
                        break
                except Exception as e:
                    print(f'  Error checking password "{pwd}": {e}')
    
    conn.close()

if __name__ == "__main__":
    check_passwords()
