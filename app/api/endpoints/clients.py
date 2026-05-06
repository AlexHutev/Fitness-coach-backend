from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.client import (
    Client,
    ClientAccountCreate,
    ClientCreate,
    ClientSummary,
    ClientUpdate,
)
from app.services.client_account_service import ClientAccountService
from app.services.client_service import ClientService
from app.utils.deps import get_current_trainer

router = APIRouter()


@router.post("/with-account", status_code=status.HTTP_201_CREATED)
async def create_client_with_account(
    client_create: ClientCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client together with a login account."""
    try:
        user, client, temp_password = await ClientAccountService.create_client_account(
            db=db,
            trainer_id=current_user.id,
            client_data=client_create,
            custom_password=client_create.custom_password,
        )
        return {
            "client": client,
            "user_account": {
                "id": user.id,
                "email": user.email,
                "temporary_password": temp_password,
            },
            "message": "Client account created. Share the temporary password with your client.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create client account: {e}",
        )


@router.post("/{client_id}/create-account", status_code=status.HTTP_201_CREATED)
async def create_account_for_existing_client(
    client_id: int,
    account_data: ClientAccountCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    """Create a login account for an existing client record."""
    client = await ClientService.get_client_by_id(
        db=db, client_id=client_id, trainer_id=current_user.id
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    try:
        user, temp_password = await ClientAccountService.link_existing_client_to_account(
            db=db,
            client_id=client_id,
            email=account_data.email,
            custom_password=account_data.custom_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "user_account": {
            "id": user.id,
            "email": user.email,
            "temporary_password": temp_password,
        },
        "message": "Account created and linked to client successfully.",
    }


@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_create: ClientCreate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService.create_client(
        db=db, client_create=client_create, trainer_id=current_user.id
    )


@router.get("/", response_model=List[ClientSummary])
async def get_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    if search:
        return await ClientService.search_clients(
            db=db,
            trainer_id=current_user.id,
            search_term=search,
            skip=skip,
            limit=limit,
        )
    return await ClientService.get_clients_by_trainer(
        db=db,
        trainer_id=current_user.id,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )


@router.get("/count")
async def get_client_count(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    count = await ClientService.get_client_count(
        db=db, trainer_id=current_user.id, active_only=active_only
    )
    return {"count": count}


@router.get("/{client_id}", response_model=Client)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    client = await ClientService.get_client_by_id(
        db=db, client_id=client_id, trainer_id=current_user.id
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return client


@router.put("/{client_id}", response_model=Client)
async def update_client(
    client_id: int,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    return await ClientService.update_client(
        db=db,
        client_id=client_id,
        trainer_id=current_user.id,
        client_update=client_update,
    )


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_trainer),
    db: AsyncSession = Depends(get_db),
):
    success = await ClientService.delete_client(
        db=db, client_id=client_id, trainer_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete client"
        )
    return {"message": "Client deleted successfully"}
