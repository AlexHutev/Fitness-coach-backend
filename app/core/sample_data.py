from sqlalchemy.orm import Session
from app.models.program import Exercise
from app.models.user import User
import json


def seed_sample_exercises(db: Session):
    """Seed the database with sample exercises"""
    
    # Check if exercises already exist
    existing_exercises = db.query(Exercise).count()
    if existing_exercises > 0:
        print("Sample exercises already exist, skipping seeding...")
        return
    
    # Get the first trainer user to assign as creator
    from app.models.user import UserRole
    trainer = db.query(User).filter(User.role == UserRole.TRAINER).first()
    if not trainer:
        print("No trainer found, creating sample exercises with creator_id=1")
        creator_id = 1
    else:
        creator_id = trainer.id
    
    sample_exercises = [
        # Push exercises
        {
            "name": "Push-ups",
            "description": "Classic bodyweight exercise for chest, shoulders, and triceps",
            "instructions": "Start in plank position. Lower your body until chest nearly touches floor. Push back up to starting position.",
            "muscle_groups": json.dumps(["chest", "shoulders", "triceps"]),
            "equipment": json.dumps(["bodyweight"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Bench Press",
            "description": "Fundamental barbell exercise for chest development",
            "instructions": "Lie on bench, grip barbell slightly wider than shoulders. Lower to chest, press back up.",
            "muscle_groups": json.dumps(["chest", "shoulders", "triceps"]),
            "equipment": json.dumps(["barbell", "bench"]),
            "difficulty_level": "intermediate",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Dumbbell Chest Press",
            "description": "Dumbbell variation of the bench press",
            "instructions": "Lie on bench with dumbbells. Press weights up and together, lower with control.",
            "muscle_groups": json.dumps(["chest", "shoulders", "triceps"]),
            "equipment": json.dumps(["dumbbells", "bench"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        },
        # Pull exercises
        {
            "name": "Pull-ups",
            "description": "Bodyweight exercise for back and biceps",
            "instructions": "Hang from bar with palms facing away. Pull body up until chin clears bar.",
            "muscle_groups": json.dumps(["back", "biceps"]),
            "equipment": json.dumps(["pull_up_bar"]),
            "difficulty_level": "intermediate",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Bent-over Rows",
            "description": "Compound exercise for back development",
            "instructions": "Bend over with barbell, pull weight to lower chest, squeeze shoulder blades.",
            "muscle_groups": json.dumps(["back", "biceps"]),
            "equipment": json.dumps(["barbell"]),
            "difficulty_level": "intermediate",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Lat Pulldowns",
            "description": "Cable exercise targeting the latissimus dorsi",
            "instructions": "Sit at cable machine, pull bar down to upper chest with wide grip.",
            "muscle_groups": json.dumps(["back", "biceps"]),
            "equipment": json.dumps(["cable_machine"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        },
        # Leg exercises
        {
            "name": "Squats",
            "description": "Fundamental lower body exercise",
            "instructions": "Stand with feet shoulder-width apart. Lower hips back and down, keep chest up.",
            "muscle_groups": json.dumps(["quads", "glutes", "hamstrings"]),
            "equipment": json.dumps(["bodyweight"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Deadlifts",
            "description": "Compound exercise for posterior chain",
            "instructions": "Stand with barbell over feet. Hinge at hips, keep back straight, lift weight.",
            "muscle_groups": json.dumps(["hamstrings", "glutes", "back"]),
            "equipment": json.dumps(["barbell"]),
            "difficulty_level": "advanced",
            "is_public": True,
            "created_by": creator_id
        },
        {
            "name": "Lunges",
            "description": "Unilateral leg exercise",
            "instructions": "Step forward into lunge position, lower back knee toward ground, return to start.",
            "muscle_groups": json.dumps(["quads", "glutes", "hamstrings"]),
            "equipment": json.dumps(["bodyweight"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        },
        # Core exercises
        {
            "name": "Plank",
            "description": "Isometric core strengthening exercise",
            "instructions": "Hold push-up position with straight line from head to heels.",
            "muscle_groups": json.dumps(["abs", "core"]),
            "equipment": json.dumps(["bodyweight"]),
            "difficulty_level": "beginner",
            "is_public": True,
            "created_by": creator_id
        }
    ]
    
    # Create exercise objects
    for exercise_data in sample_exercises:
        exercise = Exercise(**exercise_data)
        db.add(exercise)
    
    db.commit()
    print(f"Successfully seeded {len(sample_exercises)} sample exercises!")
