import secrets
import string
from typing import List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.client import ClientCreate


class ClientAccountService:
    """Manages client user accounts and links them to client records."""

    @staticmethod
    def generate_temp_password(length: int = 8) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    async def create_client_account(
        db: AsyncSession,
        trainer_id: int,
        client_data: ClientCreate,
        custom_password: Optional[str] = None,
    ) -> Tuple[User, Client, str]:
        temp_password = custom_password or ClientAccountService.generate_temp_password()

        client_user = User(
            email=client_data.email,
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            phone_number=client_data.phone_number,
            hashed_password=get_password_hash(temp_password),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False,
        )
        db.add(client_user)
        await db.flush()

        client = Client(
            trainer_id=trainer_id,
            user_id=client_user.id,
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            email=client_data.email,
            phone_number=client_data.phone_number,
            date_of_birth=client_data.date_of_birth,
            gender=client_data.gender,
            height=client_data.height,
            weight=client_data.weight,
            body_fat_percentage=client_data.body_fat_percentage,
            activity_level=client_data.activity_level,
            primary_goal=client_data.primary_goal,
            secondary_goals=client_data.secondary_goals,
            medical_conditions=client_data.medical_conditions,
            injuries=client_data.injuries,
            emergency_contact_name=client_data.emergency_contact_name,
            emergency_contact_phone=client_data.emergency_contact_phone,
            notes=client_data.notes,
        )
        db.add(client)
        await db.commit()
        await db.refresh(client_user)
        await db.refresh(client)

        return client_user, client, temp_password

    @staticmethod
    async def get_client_by_user_id(db: AsyncSession, user_id: int) -> Optional[Client]:
        result = await db.execute(select(Client).where(Client.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_trainer_clients_with_accounts(
        db: AsyncSession, trainer_id: int
    ) -> List[Client]:
        result = await db.execute(
            select(Client).where(
                and_(Client.trainer_id == trainer_id, Client.is_active.is_(True))
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def link_existing_client_to_account(
        db: AsyncSession,
        client_id: int,
        email: str,
        custom_password: Optional[str] = None,
    ) -> Tuple[User, str]:
        client = (
            await db.execute(select(Client).where(Client.id == client_id))
        ).scalar_one_or_none()
        if not client:
            raise ValueError("Client not found")
        if client.user_id:
            raise ValueError("Client already has a linked account")

        temp_password = custom_password or ClientAccountService.generate_temp_password()

        client_user = User(
            email=email,
            first_name=client.first_name,
            last_name=client.last_name,
            phone_number=client.phone_number,
            hashed_password=get_password_hash(temp_password),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False,
        )
        db.add(client_user)
        await db.flush()

        client.user_id = client_user.id
        client.email = email

        await db.commit()
        await db.refresh(client_user)
        await db.refresh(client)

        return client_user, temp_password
