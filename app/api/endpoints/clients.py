from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.client import (
    Client, ClientCreate, ClientUpdate, ClientSummary, ClientAccountCreate
)
from app.services.client_service import ClientService
from app.services.client_account_service import ClientAccountService
from app.utils.deps import get_current_trainer
from app.models.user import User

router = APIRouter()


@router.post("/with-account", status_code=status.HTTP_201_CREATED)
def create_client_with_account(
    client_create: ClientCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a new client with a login account"""
    try:
        user, client, temp_password = ClientAccountService.create_client_account(
            db=db,
            trainer_id=current_user.id,
            client_data=client_create
        )
        
        return {
            "client": client,
            "user_account": {
                "id": user.id,
                "email": user.email,
                "temporary_password": temp_password
            },
            "message": "Client account created successfully. Share the temporary password with your client."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create client account: {str(e)}"
        )


@router.post("/{client_id}/create-account", status_code=status.HTTP_201_CREATED)
def create_account_for_existing_client(
    client_id: int,
    account_data: ClientAccountCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a login account for an existing client"""
    try:
        # Verify client belongs to trainer
        client = ClientService.get_client_by_id(
            db=db,
            client_id=client_id,
            trainer_id=current_user.id
        )
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        user, temp_password = ClientAccountService.link_existing_client_to_account(
            db=db,
            client_id=client_id,
            email=account_data.email,
            custom_password=account_data.custom_password
        )
        
        return {
            "user_account": {
                "id": user.id,
                "email": user.email,
                "temporary_password": temp_password
            },
            "message": "Account created and linked to client successfully."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )


@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(
    client_create: ClientCreate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a new client"""
    client = ClientService.create_client(
        db=db, 
        client_create=client_create, 
        trainer_id=current_user.id
    )
    return client


@router.get("/", response_model=List[ClientSummary])
def get_clients(
    skip: int = Query(0, ge=0, description="Number of clients to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of clients to return"),
    active_only: bool = Query(True, description="Return only active clients"),
    search: Optional[str] = Query(None, description="Search term for client name or email"),
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get all clients for the current trainer"""
    
    if search:
        clients = ClientService.search_clients(
            db=db,
            trainer_id=current_user.id,
            search_term=search,
            skip=skip,
            limit=limit
        )
    else:
        clients = ClientService.get_clients_by_trainer(
            db=db,
            trainer_id=current_user.id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    
    return clients


@router.get("/count")
def get_client_count(
    active_only: bool = Query(True, description="Count only active clients"),
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get total client count for the current trainer"""
    count = ClientService.get_client_count(
        db=db,
        trainer_id=current_user.id,
        active_only=active_only
    )
    return {"count": count}


@router.get("/{client_id}", response_model=Client)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get a specific client by ID"""
    client = ClientService.get_client_by_id(
        db=db,
        client_id=client_id,
        trainer_id=current_user.id
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return client


@router.put("/{client_id}", response_model=Client)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update a client"""
    client = ClientService.update_client(
        db=db,
        client_id=client_id,
        trainer_id=current_user.id,
        client_update=client_update
    )
    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a client"""
    success = ClientService.delete_client(
        db=db,
        client_id=client_id,
        trainer_id=current_user.id
    )
    
    if success:
        return {"message": "Client deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete client"
        )
