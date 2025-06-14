from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.program import Program
from app.models.user import User
from app.schemas.program import ProgramCreate, ProgramUpdate, ProgramList
import json


class ProgramService:
    
    @staticmethod
    def create_program(db: Session, program_data: ProgramCreate, trainer_id: int) -> Program:
        """Create a new training program."""
        # Convert workout_structure to JSON for storage
        workout_structure_json = [day.dict() for day in program_data.workout_structure]
        
        # Convert equipment list to JSON string
        equipment_json = json.dumps(program_data.equipment_needed) if program_data.equipment_needed else None
        
        program = Program(
            trainer_id=trainer_id,
            name=program_data.name,
            description=program_data.description,
            program_type=program_data.program_type,
            difficulty_level=program_data.difficulty_level,
            duration_weeks=program_data.duration_weeks,
            sessions_per_week=program_data.sessions_per_week,
            workout_structure=workout_structure_json,
            tags=program_data.tags,
            equipment_needed=equipment_json,
            is_template=program_data.is_template
        )
        
        db.add(program)
        db.commit()
        db.refresh(program)
        return program
    
    @staticmethod
    def get_program(db: Session, program_id: int, trainer_id: Optional[int] = None) -> Optional[Program]:
        """Get a specific program by ID."""
        query = db.query(Program).filter(Program.id == program_id)
        
        # If trainer_id is provided, ensure the program belongs to this trainer
        if trainer_id is not None:
            query = query.filter(Program.trainer_id == trainer_id)
            
        return query.first()
    
    @staticmethod
    def get_programs(
        db: Session, 
        trainer_id: int, 
        skip: int = 0, 
        limit: int = 100,
        program_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_template: Optional[bool] = None
    ) -> List[Program]:
        """Get programs for a trainer with optional filtering."""
        query = db.query(Program).filter(
            and_(
                Program.trainer_id == trainer_id,
                Program.is_active == True
            )
        )
        
        # Apply filters
        if program_type:
            query = query.filter(Program.program_type == program_type)
        if difficulty_level:
            query = query.filter(Program.difficulty_level == difficulty_level)
        if is_template is not None:
            query = query.filter(Program.is_template == is_template)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_program(
        db: Session, 
        program_id: int, 
        program_data: ProgramUpdate, 
        trainer_id: int
    ) -> Optional[Program]:
        """Update a program."""
        program = ProgramService.get_program(db, program_id, trainer_id)
        if not program:
            return None
        
        # Update fields that were provided
        update_data = program_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "workout_structure" and value is not None:
                # Convert workout_structure to JSON for storage
                value = [day.dict() for day in value]
            elif field == "equipment_needed" and value is not None:
                # Convert equipment list to JSON string
                value = json.dumps(value)
            
            setattr(program, field, value)
        
        db.commit()
        db.refresh(program)
        return program
    
    @staticmethod
    def delete_program(db: Session, program_id: int, trainer_id: int) -> bool:
        """Soft delete a program (set is_active = False)."""
        program = ProgramService.get_program(db, program_id, trainer_id)
        if not program:
            return False
        
        program.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def duplicate_program(db: Session, program_id: int, trainer_id: int, new_name: str) -> Optional[Program]:
        """Create a copy of an existing program."""
        original_program = ProgramService.get_program(db, program_id, trainer_id)
        if not original_program:
            return None
        
        # Create new program with same data but new name
        new_program = Program(
            trainer_id=trainer_id,
            name=new_name,
            description=original_program.description,
            program_type=original_program.program_type,
            difficulty_level=original_program.difficulty_level,
            duration_weeks=original_program.duration_weeks,
            sessions_per_week=original_program.sessions_per_week,
            workout_structure=original_program.workout_structure,
            tags=original_program.tags,
            equipment_needed=original_program.equipment_needed,
            is_template=True  # Duplicates are always templates initially
        )
        
        db.add(new_program)
        db.commit()
        db.refresh(new_program)
        return new_program
    
    @staticmethod
    def search_programs(db: Session, trainer_id: int, search_term: str) -> List[Program]:
        """Search programs by name, description, or tags."""
        return db.query(Program).filter(
            and_(
                Program.trainer_id == trainer_id,
                Program.is_active == True,
                or_(
                    Program.name.ilike(f"%{search_term}%"),
                    Program.description.ilike(f"%{search_term}%"),
                    Program.tags.ilike(f"%{search_term}%")
                )
            )
        ).all()
