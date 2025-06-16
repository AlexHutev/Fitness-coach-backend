#!/usr/bin/env python3
"""Start the FastAPI server with proper environment setup"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
