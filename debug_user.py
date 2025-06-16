#!/usr/bin/env python3
"""
Debug script to check user role
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole

def debug_user():
    """Debug user role"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == 'trainer@fitnesscoach.com').first()
        if user:
            print(f'User found: {user.email}')
            print(f'Role: {user.role}')
            print(f'Role type: {type(user.role)}')
            print(f'Role value: {user.role.value if hasattr(user.role, "value") else "N/A"}')
            print(f'Is active: {user.is_active}')
            print(f'UserRole.TRAINER: {UserRole.TRAINER}')
            print(f'UserRole.TRAINER type: {type(UserRole.TRAINER)}')
            print(f'UserRole.TRAINER value: {UserRole.TRAINER.value}')
            print(f'Comparison user.role == UserRole.TRAINER: {user.role == UserRole.TRAINER}')
            print(f'Comparison user.role != UserRole.TRAINER: {user.role != UserRole.TRAINER}')
        else:
            print('User not found')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    debug_user()
