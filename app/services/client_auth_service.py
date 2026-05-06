from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Client, Program, ProgramAssignment, User  # noqa: F401
from app.models.program_assignment import AssignmentStatus
from app.schemas.client_schemas import (
    ClientCreateCredentials,  # noqa: F401
    ClientLoginRequest,
    ClientTokenResponse,
)


class ClientAuthService:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_client_access_token(self, assignment_id: int, client_id: int) -> str:
        now = datetime.now(timezone.utc)
        data = {
            "sub": str(client_id),
            "assignment_id": assignment_id,
            "type": "client_access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)

    def verify_client_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            client_id = payload.get("sub")
            assignment_id = payload.get("assignment_id")
            token_type = payload.get("type")
            if client_id is None or assignment_id is None or token_type != "client_access":
                return None
            return {
                "client_id": int(client_id),
                "assignment_id": assignment_id,
                "token_type": token_type,
            }
        except JWTError:
            return None

    async def authenticate_client(
        self, db: AsyncSession, email: str, password: str
    ) -> Optional[ProgramAssignment]:
        stmt = (
            select(ProgramAssignment)
            .where(ProgramAssignment.client_access_email == email)
            .where(ProgramAssignment.status == AssignmentStatus.ACTIVE)
        )
        assignment = (await db.execute(stmt)).scalar_one_or_none()

        if not assignment or not assignment.client_hashed_password:
            return None
        if not self.verify_password(password, assignment.client_hashed_password):
            return None
        return assignment

    async def login_client(
        self, db: AsyncSession, login_request: ClientLoginRequest
    ) -> Optional[ClientTokenResponse]:
        assignment = await self.authenticate_client(
            db, login_request.email, login_request.password
        )
        if not assignment:
            return None

        program = (
            await db.execute(select(Program).where(Program.id == assignment.program_id))
        ).scalar_one_or_none()
        if not program:
            return None

        access_token = self.create_client_access_token(assignment.id, assignment.client_id)
        return ClientTokenResponse(
            access_token=access_token,
            token_type="bearer",
            client_id=assignment.client_id,
            assignment_id=assignment.id,
            program_name=program.name,
        )

    async def create_client_credentials(
        self,
        db: AsyncSession,
        assignment_id: int,
        email: str,
        password: str,
    ) -> bool:
        assignment = (
            await db.execute(
                select(ProgramAssignment).where(ProgramAssignment.id == assignment_id)
            )
        ).scalar_one_or_none()
        if not assignment:
            return False

        existing = (
            await db.execute(
                select(ProgramAssignment)
                .where(ProgramAssignment.client_access_email == email)
                .where(ProgramAssignment.id != assignment_id)
            )
        ).scalar_one_or_none()
        if existing:
            return False

        assignment.client_access_email = email
        assignment.client_hashed_password = self.get_password_hash(password)
        await db.commit()
        await db.refresh(assignment)
        return True

    async def get_client_assignment_from_token(
        self, db: AsyncSession, token: str
    ) -> Optional[ProgramAssignment]:
        token_data = self.verify_client_token(token)
        if not token_data:
            return None
        stmt = (
            select(ProgramAssignment)
            .where(ProgramAssignment.id == token_data["assignment_id"])
            .where(ProgramAssignment.client_id == token_data["client_id"])
            .where(ProgramAssignment.status == AssignmentStatus.ACTIVE)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update_client_password(
        self, db: AsyncSession, assignment_id: int, new_password: str
    ) -> bool:
        assignment = (
            await db.execute(
                select(ProgramAssignment).where(ProgramAssignment.id == assignment_id)
            )
        ).scalar_one_or_none()
        if not assignment:
            return False
        assignment.client_hashed_password = self.get_password_hash(new_password)
        await db.commit()
        return True


client_auth_service = ClientAuthService()
