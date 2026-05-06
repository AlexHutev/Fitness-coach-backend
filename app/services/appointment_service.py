from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import and_, asc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.schedule import Appointment, AppointmentStatus
from app.schemas.schedule import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_appointment(
        self, appointment_data: AppointmentCreate, trainer_id: int
    ) -> Appointment:
        client_result = await self.db.execute(
            select(Client).where(
                and_(
                    Client.id == appointment_data.client_id,
                    Client.trainer_id == trainer_id,
                )
            )
        )
        if client_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=404,
                detail="Client not found or not assigned to this trainer",
            )

        # Time-conflict check
        conflict_stmt = select(Appointment).where(
            and_(
                Appointment.trainer_id == trainer_id,
                Appointment.status != AppointmentStatus.CANCELLED.value,
                or_(
                    and_(
                        Appointment.start_time <= appointment_data.start_time,
                        Appointment.end_time > appointment_data.start_time,
                    ),
                    and_(
                        Appointment.start_time < appointment_data.end_time,
                        Appointment.end_time >= appointment_data.end_time,
                    ),
                    and_(
                        Appointment.start_time >= appointment_data.start_time,
                        Appointment.end_time <= appointment_data.end_time,
                    ),
                ),
            )
        )
        conflict = (await self.db.execute(conflict_stmt)).scalar_one_or_none()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Time conflict with existing appointment at {conflict.start_time}",
            )

        appointment = Appointment(trainer_id=trainer_id, **appointment_data.model_dump())
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get_appointments(
        self,
        trainer_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Appointment], int]:
        base = select(Appointment).where(Appointment.trainer_id == trainer_id)

        if date_from:
            base = base.where(
                Appointment.start_time >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to:
            base = base.where(
                Appointment.start_time
                < datetime.combine(date_to + timedelta(days=1), datetime.min.time())
            )
        if status:
            base = base.where(Appointment.status == status)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_stmt)).scalar_one())

        list_stmt = (
            base.options(
                selectinload(Appointment.client),
                selectinload(Appointment.trainer),
            )
            .order_by(asc(Appointment.start_time))
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(list_stmt)
        return list(result.scalars().all()), total

    async def get_todays_appointments(self, trainer_id: int) -> List[Appointment]:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.client),
                selectinload(Appointment.trainer),
            )
            .where(
                and_(
                    Appointment.trainer_id == trainer_id,
                    Appointment.start_time >= datetime.combine(today, datetime.min.time()),
                    Appointment.start_time < datetime.combine(tomorrow, datetime.min.time()),
                    Appointment.status != AppointmentStatus.CANCELLED.value,
                )
            )
            .order_by(asc(Appointment.start_time))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_appointment(
        self, appointment_id: int, trainer_id: int
    ) -> Optional[Appointment]:
        stmt = (
            select(Appointment)
            .options(
                selectinload(Appointment.client),
                selectinload(Appointment.trainer),
            )
            .where(
                and_(
                    Appointment.id == appointment_id,
                    Appointment.trainer_id == trainer_id,
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_appointment(
        self,
        appointment_id: int,
        trainer_id: int,
        appointment_data: AppointmentUpdate,
    ) -> Optional[Appointment]:
        appointment = await self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return None

        for field, value in appointment_data.model_dump(exclude_unset=True).items():
            setattr(appointment, field, value)
        appointment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def delete_appointment(self, appointment_id: int, trainer_id: int) -> bool:
        appointment = await self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return False
        await self.db.delete(appointment)
        await self.db.commit()
        return True

    async def update_appointment_status(
        self,
        appointment_id: int,
        trainer_id: int,
        status: AppointmentStatus,
    ) -> Optional[Appointment]:
        appointment = await self.get_appointment(appointment_id, trainer_id)
        if not appointment:
            return None
        appointment.status = status.value if hasattr(status, "value") else status
        appointment.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment
