import sys
import os
import subprocess

# Change to the correct directory
os.chdir('C:/university/fitness-coach')

# Start the FastAPI server
try:
    print("Starting FastAPI server...")
    result = subprocess.run([
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', '--reload', '--port', '8000'
    ], cwd='C:/university/fitness-coach')
except Exception as e:
    print(f"Error starting server: {e}")
