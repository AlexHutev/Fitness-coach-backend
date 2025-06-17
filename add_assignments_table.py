#!/usr/bin/env python3
"""
Add program_assignments table to existing database
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, MetaData, inspect
from app.core.config import settings
from app.core.database import Base
from app.models import *  # Import all models including new ProgramAssignment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_database():
    """Check what tables currently exist"""
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("Current tables in database:")
        for table in tables:
            logger.info(f"  - {table}")
            
        return tables
    except Exception as e:
        logger.error(f"Error inspecting database: {e}")
        return []


def add_missing_tables():
    """Add any missing tables (like program_assignments)"""
    try:
        engine = create_engine(settings.database_url)
        
        # This will only create tables that don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Missing tables created successfully")
        
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Error creating missing tables: {e}")
        return False


def main():
    """Main function"""
    logger.info("Inspecting current database...")
    
    current_tables = inspect_database()
    
    if 'program_assignments' in current_tables:
        logger.info("program_assignments table already exists")
    else:
        logger.info("program_assignments table not found, creating...")
        if add_missing_tables():
            logger.info("program_assignments table created successfully!")
        else:
            logger.error("Failed to create program_assignments table")
            sys.exit(1)
    
    # Final inspection
    logger.info("\nFinal database inspection:")
    inspect_database()


if __name__ == "__main__":
    main()
