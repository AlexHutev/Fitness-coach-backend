from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from typing import List, Optional


class ClientService:
    @staticmethod
    def create_client(db: Session, client_create: ClientCreate, trainer_id: int) -> Client:
        """Create a new client for a trainer"""
        
        db_client = Client(
            trainer_id=trainer_id,
            **client_create.dict()
        )
        
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    
    @staticmethod
    def get_client_by_id(db: Session, client_id: int, trainer_id: int) -> Optional[Client]:
        """Get client by ID (only if belongs to trainer)"""
        return db.query(Client).filter(
            Client.id == client_id,
            Client.trainer_id == trainer_id
        ).first()
    
    @staticmethod
    def get_clients_by_trainer(
        db: Session, 
        trainer_id: int, 
        skip: int = 0, 
        limit: int = 100,
        active_only: bool = True
    ) -> List[Client]:
        """Get all clients for a trainer"""
        query = db.query(Client).filter(Client.trainer_id == trainer_id)
        
        if active_only:
            query = query.filter(Client.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_client(
        db: Session, 
        client_id: int, 
        trainer_id: int, 
        client_update: ClientUpdate
    ) -> Client:
        """Update client information"""
        client = db.query(Client).filter(
            Client.id == client_id,
            Client.trainer_id == trainer_id
        ).first()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        # Update fields
        update_data = client_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        
        db.commit()
        db.refresh(client)
        return client
    
    @staticmethod
    def delete_client(db: Session, client_id: int, trainer_id: int) -> bool:
        """Soft delete client (mark as inactive)"""
        client = db.query(Client).filter(
            Client.id == client_id,
            Client.trainer_id == trainer_id
        ).first()
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        client.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def search_clients(
        db: Session, 
        trainer_id: int, 
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Client]:
        """Search clients by name or email"""
        search_pattern = f"%{search_term}%"
        
        return db.query(Client).filter(
            Client.trainer_id == trainer_id,
            Client.is_active == True,
            (
                Client.first_name.ilike(search_pattern) |
                Client.last_name.ilike(search_pattern) |
                Client.email.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_client_count(db: Session, trainer_id: int, active_only: bool = True) -> int:
        """Get total client count for a trainer"""
        query = db.query(Client).filter(Client.trainer_id == trainer_id)
        
        if active_only:
            query = query.filter(Client.is_active == True)
        
        return query.count()
