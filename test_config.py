#!/usr/bin/env python3
"""Test configuration loading"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test loading the .env file directly
from dotenv import load_dotenv
load_dotenv()

print("Environment variables from .env:")
print(f"DATABASE_URL: {repr(os.getenv('DATABASE_URL'))}")

# Test the config
try:
    from app.core.config import settings
    print(f"\nSettings loaded:")
    print(f"database_url: {repr(settings.database_url)}")
    print(f"database_url_computed: {settings.database_url_computed}")
except Exception as e:
    print(f"Error loading settings: {e}")
