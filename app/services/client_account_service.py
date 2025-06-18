from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User, UserRole
from app.models.client import Client
from app.core.security import get_password_hash
from app.schemas.user import UserCreate
from app.schemas.client import ClientCreate
import secrets
import string
from typing import Optional


class ClientAccountService:
    """Service for managing client user accounts and linking them to client records"""
    
    @staticmethod
    def generate_temp_password(length: int = 8) -> str:
        """Generate a temporary password for new client accounts"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def create_client_account(
        db: Session,
        trainer_id: int,
        client_data: ClientCreate,
        custom_password: Optional[str] = None
    ) -> tuple[User, Client, str]:
        """
        Create both a client record and a user account for the client.
        Returns (user, client, temporary_password)
        """
        
        # Generate temporary password if not provided
        temp_password = custom_password or ClientAccountService.generate_temp_password()
        
        # Create user account for client
        client_user = User(
            email=client_data.email,
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            phone_number=client_data.phone_number,
            hashed_password=get_password_hash(temp_password),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False  # Client should verify on first login
        )
        
        db.add(client_user)
        db.flush()  # Get the user ID
        
        # Create client record linked to user account
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
            notes=client_data.notes
        )
        
        db.add(client)
        db.commit()
        db.refresh(client_user)
        db.refresh(client)
        
        return client_user, client, temp_password
    
    @staticmethod
    def get_client_by_user_id(db: Session, user_id: int) -> Optional[Client]:
        """Get client record by user account ID"""
        return db.query(Client).filter(Client.user_id == user_id).first()
    
    @staticmethod
    def get_trainer_clients_with_accounts(db: Session, trainer_id: int):
        """Get all clients for a trainer, including their user account info"""
        return db.query(Client).filter(
            and_(
                Client.trainer_id == trainer_id,
                Client.is_active == True
            )
        ).all()
    
    @staticmethod
    def link_existing_client_to_account(
        db: Session,
        client_id: int,
        email: str,
        custom_password: Optional[str] = None
    ) -> tuple[User, str]:
        """Link an existing client record to a new user account"""
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client not found")
        
        if client.user_id:
            raise ValueError("Client already has a linked account")
        
        # Generate temporary password
        temp_password = custom_password or ClientAccountService.generate_temp_password()
        
        # Create user account
        client_user = User(
            email=email,
            first_name=client.first_name,
            last_name=client.last_name,
            phone_number=client.phone_number,
            hashed_password=get_password_hash(temp_password),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=False
        )
        
        db.add(client_user)
        db.flush()
        
        # Link to client record
        client.user_id = client_user.id
        client.email = email  # Update client email if different
        
        db.commit()
        db.refresh(client_user)
        db.refresh(client)
        
        return client_user, temp_password
