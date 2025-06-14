#!/usr/bin/env python3
"""
Database initialization and setup script for FitnessCoach API
This version handles different MySQL configurations
"""

import sys
import os
from pathlib import Path
import getpass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text
    from app.core.config import settings
    from app.core.database import Base
    from app.models import *  # Import all models
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed all requirements: pip install -r requirements.txt")
    sys.exit(1)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_root_password():
    """Get MySQL root password from user"""
    print("Please enter your MySQL root password (or press Enter if no password):")
    password = getpass.getpass("MySQL root password: ")
    return password


def create_database_with_root(password=""):
    """Create the database using root credentials"""
    try:
        # Connect to MySQL server (not specific database)
        if password:
            engine_url = f"mysql+pymysql://root:{password}@{settings.db_host}:{settings.db_port}"
        else:
            engine_url = f"mysql+pymysql://root@{settings.db_host}:{settings.db_port}"
        
        engine = create_engine(engine_url)
        
        with engine.connect() as conn:
            # Create database if it doesn't exist
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.db_name}"))
            logger.info(f"Database '{settings.db_name}' created or already exists")
            
            # Create user if it doesn't exist
            try:
                conn.execute(text(f"CREATE USER IF NOT EXISTS '{settings.db_user}'@'localhost' IDENTIFIED BY '{settings.db_password}'"))
                logger.info(f"User '{settings.db_user}' created or already exists")
            except Exception as e:
                logger.warning(f"User creation warning: {e}")
            
            # Grant privileges
            conn.execute(text(f"GRANT ALL PRIVILEGES ON {settings.db_name}.* TO '{settings.db_user}'@'localhost'"))
            conn.execute(text("FLUSH PRIVILEGES"))
            logger.info("Privileges granted")
            
            conn.commit()
        
        engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database with root: {e}")
        return False


def test_user_connection():
    """Test if we can connect with the application user"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        logger.info("Application user connection successful")
        return True
    except Exception as e:
        logger.error(f"Application user connection failed: {e}")
        return False


def create_tables():
    """Create all tables"""
    try:
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("Starting database setup...")
    logger.info(f"Target database: {settings.db_name}")
    logger.info(f"Target user: {settings.db_user}")
    
    # First try to connect with application user (maybe database already exists)
    if test_user_connection():
        logger.info("Database and user already configured!")
    else:
        logger.info("Setting up database and user...")
        
        # Try with empty password first
        if not create_database_with_root(""):
            # If that fails, ask for password
            root_password = get_root_password()
            if not create_database_with_root(root_password):
                logger.error("Failed to create database. Please check MySQL root credentials.")
                sys.exit(1)
        
        # Test connection again
        if not test_user_connection():
            logger.error("Database created but can't connect with application user")
            sys.exit(1)
    
    # Create tables
    if not create_tables():
        logger.error("Failed to create tables")
        sys.exit(1)
    
    logger.info("✅ Database setup completed successfully!")
    print()
    print("📋 Database Information:")
    print(f"   Database: {settings.db_name}")
    print(f"   User: {settings.db_user}")
    print(f"   Host: {settings.db_host}:{settings.db_port}")
    print()
    print("🎯 Next steps:")
    print("   1. Run: python -m alembic stamp head")
    print("   2. Run: python create_sample_users.py")
    print("   3. Run: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
