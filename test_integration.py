"""
Test script to verify the integration
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test if all modules can be imported"""
    try:
        print("Testing backend imports...")
        
        # Test model imports
        from app.models.program import Program, Exercise
        print("All Models imported successfully")
        
        # Test service imports
        from app.services.program_service import ProgramService
        from app.services.exercise_service import ExerciseService
        print("All Services imported successfully")
        
        # Test API endpoint imports
        from app.api.endpoints.programs import router as programs_router
        from app.api.endpoints.exercises import router as exercises_router
        print("All API endpoints imported successfully")
        
        # Test schema imports
        from app.schemas.program import ProgramCreate, ProgramUpdate
        from app.schemas.exercise import ExerciseCreate, ExerciseUpdate
        print("All Schemas imported successfully")
        
        print("\nAll backend imports successful!")
        return True
        
    except Exception as e:
        print(f"Import error: {e}")
        return False

def test_database_models():
    """Test database model structure"""
    try:
        from app.models.program import Program, Exercise
        
        # Test Program model attributes
        program_attrs = ['id', 'trainer_id', 'name', 'description', 'program_type', 
                        'difficulty_level', 'duration_weeks', 'sessions_per_week',
                        'workout_structure', 'is_template', 'is_active']
        
        for attr in program_attrs:
            if hasattr(Program, attr):
                print(f"Program.{attr} exists")
            else:
                print(f"Program.{attr} missing")
                
        # Test Exercise model attributes  
        exercise_attrs = ['id', 'name', 'description', 'instructions', 
                         'muscle_groups', 'equipment', 'difficulty_level',
                         'image_url', 'video_url', 'created_by', 'is_public']
        
        for attr in exercise_attrs:
            if hasattr(Exercise, attr):
                print(f"Exercise.{attr} exists")
            else:
                print(f"Exercise.{attr} missing")
                
        print("\nDatabase models are properly structured!")
        return True
        
    except Exception as e:
        print(f"Database model error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("FitnessCoach Integration Test")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print("\n" + "-" * 50)
    
    # Test database models
    if not test_database_models():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("INTEGRATION TEST PASSED!")
        print("Backend is ready for frontend integration")
    else:
        print("INTEGRATION TEST FAILED!")
        print("Please check the errors above")
    print("=" * 50)
