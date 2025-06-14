#!/usr/bin/env python3
"""
Database initialization and setup script for FitnessCoach API
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import *  # Import all models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database():
    """Create the database if it doesn't exist"""
    # Connect to MySQL server (not specific database)
    engine_url = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}"
    engine = create_engine(engine_url)
    
    try:
        with engine.connect() as conn:
            # Create database if it doesn't exist
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.db_name}"))
            conn.commit()
            logger.info(f"Database '{settings.db_name}' created or already exists")
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False
    finally:
        engine.dispose()
    
    return True


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
    
    # Create database
    if not create_database():
        logger.error("Failed to create database")
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        logger.error("Failed to create tables")
        sys.exit(1)
    
    logger.info("Database setup completed successfully!")
    logger.info("You can now run: alembic stamp head")
    logger.info("Then create migrations with: alembic revision --autogenerate -m 'description'")


if __name__ == "__main__":
    main()
