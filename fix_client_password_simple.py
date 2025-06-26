#!/usr/bin/env python3

import sqlite3
from passlib.context import CryptContext

def fix_client_password():
    """Fix client password using the correct hashing method"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Hash the correct password
    correct_password = "iveta123"
    hashed_password = pwd_context.hash(correct_password)
    
    # Update in database
    conn = sqlite3.connect('fitness_coach.db')
    cursor = conn.cursor()
    
    try:
        # Update client password
        cursor.execute("""
            UPDATE users 
            SET hashed_password = ? 
            WHERE email = 'iveta@gmail.com'
        """, (hashed_password,))
        
        if cursor.rowcount > 0:
            print("SUCCESS: Client password updated successfully!")
            print("Email: iveta@gmail.com")
            print("Password: iveta123")
        else:
            print("ERROR: Client user not found")
        
        conn.commit()
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_client_password()
