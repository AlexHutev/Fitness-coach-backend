#!/usr/bin/env python3
"""
Debug user authentication
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
from app.models.user import User
from app.core.security import verify_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_user_login(email: str, password: str):
    """Check if user can login with given credentials"""
    db = SessionLocal()
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.error(f"User with email {email} not found")
            return False
        
        logger.info(f"User found: {user.email}")
        logger.info(f"User active: {user.is_active}")
        logger.info(f"User verified: {user.is_verified}")
        logger.info(f"User role: {user.role}")
        
        # Check password
        password_valid = verify_password(password, user.hashed_password)
        logger.info(f"Password valid: {password_valid}")
        
        if password_valid and user.is_active:
            logger.info("✅ Login should work!")
            return True
        else:
            logger.error("❌ Login should fail!")
            return False
        
    except Exception as e:
        logger.error(f"Error checking user: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function"""
    logger.info("Checking user credentials...")
    
    # Test trainer account
    logger.info("\n=== Testing trainer@fitnesscoach.com ===")
    check_user_login("trainer@fitnesscoach.com", "trainer123")
    
    # Test admin account
    logger.info("\n=== Testing admin@fitnesscoach.com ===")
    check_user_login("admin@fitnesscoach.com", "admin123")
    
    # List all users
    logger.info("\n=== All users in database ===")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            logger.info(f"Email: {user.email}, Active: {user.is_active}, Role: {user.role}")
    finally:
        db.close()


if __name__ == "__main__":
    main()