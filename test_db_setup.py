#!/usr/bin/env python3
"""
Simple script to test database connection and create tables
Run this AFTER setting up the database manually
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text
    from app.core.config import settings
    from app.core.database import Base
    from app.models import *  # Import all models
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you've installed all requirements: pip install -r requirements.txt")
    sys.exit(1)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """Test database connection"""
    try:
        engine = create_engine(settings.database_url_computed)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'Connection successful!' as status"))
            row = result.fetchone()
            logger.info(f"Connection successful: {row[0]}")
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def create_tables():
    """Create all tables"""
    try:
        engine = create_engine(settings.database_url_computed)
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            if 'sqlite' in settings.database_url_computed:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            else:
                result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {', '.join(tables)}")
        
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def main():
    """Main function"""
    print("FitnessCoach Database Setup Test")
    print("=" * 40)
    print(f"Database URL: {settings.database_url_computed}")
    print("=" * 40)
    
    # Test connection
    print("\nTesting database connection...")
    if not test_connection():
        print("\nDatabase connection failed!")
        print("\nTo fix this, please:")
        print("   1. Open MySQL client or MySQL Workbench")
        print("   2. Run the SQL script: setup_database.sql")
        print("   3. Then run this script again")
        sys.exit(1)
    
    # Create tables
    print("\nCreating database tables...")
    if not create_tables():
        print("Failed to create tables")
        sys.exit(1)
    
    print("\nDatabase setup completed successfully!")
    print("\nNext steps:")
    print("   1. Initialize Alembic: python -m alembic stamp head")
    print("   2. Create sample users: python create_sample_users.py")
    print("   3. Start the API: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
