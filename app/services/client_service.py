from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    @staticmethod
    async def create_client(
        db: AsyncSession, client_create: ClientCreate, trainer_id: int
    ) -> Client:
        # `custom_password` lives on the schema for account-creation flows but
        # is not a column on the Client model — exclude before splatting.
        payload = client_create.dict(exclude={"custom_password"})
        db_client = Client(trainer_id=trainer_id, **payload)
        db.add(db_client)
        await db.commit()
        await db.refresh(db_client)
        return db_client

    @staticmethod
    async def get_client_by_id(
        db: AsyncSession, client_id: int, trainer_id: int
    ) -> Optional[Client]:
        result = await db.execute(
            select(Client).where(Client.id == client_id, Client.trainer_id == trainer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_clients_by_trainer(
        db: AsyncSession,
        trainer_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[Client]:
        stmt = select(Client).where(Client.trainer_id == trainer_id)
        if active_only:
            stmt = stmt.where(Client.is_active.is_(True))
        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update_client(
        db: AsyncSession,
        client_id: int,
        trainer_id: int,
        client_update: ClientUpdate,
    ) -> Client:
        client = await ClientService.get_client_by_id(db, client_id, trainer_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        for field, value in client_update.dict(exclude_unset=True).items():
            setattr(client, field, value)

        await db.commit()
        await db.refresh(client)
        return client

    @staticmethod
    async def delete_client(db: AsyncSession, client_id: int, trainer_id: int) -> bool:
        client = await ClientService.get_client_by_id(db, client_id, trainer_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        client.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def search_clients(
        db: AsyncSession,
        trainer_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Client]:
        pattern = f"%{search_term}%"
        stmt = (
            select(Client)
            .where(
                Client.trainer_id == trainer_id,
                Client.is_active.is_(True),
                or_(
                    Client.first_name.ilike(pattern),
                    Client.last_name.ilike(pattern),
                    Client.email.ilike(pattern),
                ),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_client_count(
        db: AsyncSession, trainer_id: int, active_only: bool = True
    ) -> int:
        stmt = select(func.count()).select_from(Client).where(Client.trainer_id == trainer_id)
        if active_only:
            stmt = stmt.where(Client.is_active.is_(True))
        result = await db.execute(stmt)
        return int(result.scalar_one())
