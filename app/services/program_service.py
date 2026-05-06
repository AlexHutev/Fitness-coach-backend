import json
import logging
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.program import Program
from app.schemas.program import ProgramCreate, ProgramUpdate

logger = logging.getLogger(__name__)


class ProgramService:
    @staticmethod
    async def create_program(
        db: AsyncSession, program_data: ProgramCreate, trainer_id: int
    ) -> Program:
        workout_structure_json = [day.dict() for day in program_data.workout_structure]
        equipment_json = (
            json.dumps(program_data.equipment_needed) if program_data.equipment_needed else None
        )

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
            is_template=program_data.is_template,
        )

        db.add(program)
        await db.commit()
        await db.refresh(program)
        return program

    @staticmethod
    async def get_program(
        db: AsyncSession, program_id: int, trainer_id: Optional[int] = None
    ) -> Optional[Program]:
        stmt = select(Program).where(Program.id == program_id)
        if trainer_id is not None:
            stmt = stmt.where(Program.trainer_id == trainer_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_programs(
        db: AsyncSession,
        trainer_id: int,
        skip: int = 0,
        limit: int = 100,
        program_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_template: Optional[bool] = None,
    ) -> List[Program]:
        stmt = select(Program).where(
            and_(Program.trainer_id == trainer_id, Program.is_active.is_(True))
        )
        if program_type:
            stmt = stmt.where(Program.program_type == program_type)
        if difficulty_level:
            stmt = stmt.where(Program.difficulty_level == difficulty_level)
        if is_template is not None:
            stmt = stmt.where(Program.is_template == is_template)

        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update_program(
        db: AsyncSession,
        program_id: int,
        program_data: ProgramUpdate,
        trainer_id: int,
    ) -> Optional[Program]:
        program = await ProgramService.get_program(db, program_id, trainer_id)
        if not program:
            return None

        for field, value in program_data.dict(exclude_unset=True).items():
            if field == "workout_structure" and value is not None:
                if isinstance(value, list) and value and hasattr(value[0], "dict"):
                    value = [day.dict() for day in value]
            elif field == "equipment_needed" and value is not None:
                value = json.dumps(value)
            setattr(program, field, value)

        await db.commit()
        await db.refresh(program)
        return program

    @staticmethod
    async def delete_program(db: AsyncSession, program_id: int, trainer_id: int) -> bool:
        program = await ProgramService.get_program(db, program_id, trainer_id)
        if not program:
            return False
        program.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def duplicate_program(
        db: AsyncSession, program_id: int, trainer_id: int, new_name: str
    ) -> Optional[Program]:
        original = await ProgramService.get_program(db, program_id, trainer_id)
        if not original:
            return None

        new_program = Program(
            trainer_id=trainer_id,
            name=new_name,
            description=original.description,
            program_type=original.program_type,
            difficulty_level=original.difficulty_level,
            duration_weeks=original.duration_weeks,
            sessions_per_week=original.sessions_per_week,
            workout_structure=original.workout_structure,
            tags=original.tags,
            equipment_needed=original.equipment_needed,
            is_template=True,
        )
        db.add(new_program)
        await db.commit()
        await db.refresh(new_program)
        return new_program

    @staticmethod
    async def search_programs(
        db: AsyncSession, trainer_id: int, search_term: str
    ) -> List[Program]:
        pattern = f"%{search_term}%"
        stmt = select(Program).where(
            and_(
                Program.trainer_id == trainer_id,
                Program.is_active.is_(True),
                or_(
                    Program.name.ilike(pattern),
                    Program.description.ilike(pattern),
                    Program.tags.ilike(pattern),
                ),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
