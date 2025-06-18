#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.program import Exercise

def main():
    db = SessionLocal()
    exercises = db.query(Exercise).all()
    print(f'Total exercises in database: {len(exercises)}')
    
    if exercises:
        print("\nExercises found:")
        for ex in exercises:
            print(f'- {ex.id}: {ex.name} (Public: {ex.is_public}, Created by: {ex.created_by})')
    else:
        print("No exercises found in database!")
        
    db.close()

if __name__ == "__main__":
    main()
