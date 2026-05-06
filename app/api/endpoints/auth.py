from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.database import get_db
from app.core.rate_limit import AUTH_RATE_LIMIT, limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models.user import User as UserModel
from app.schemas.user import (
    LoginRequest,
    PasswordChange,
    RefreshRequest,
    Token,
    User,
    UserCreate,
    UserUpdate,
)
from app.services.user_service import UserService
from app.utils.deps import get_current_active_user

router = APIRouter()


def _issue_token_pair(email: str) -> Token:
    return Token(
        access_token=create_access_token(subject=email),
        refresh_token=create_refresh_token(subject=email),
    )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new trainer account."""
    return await UserService.create_user(db=db, user_create=user_create)


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and issue an access + refresh token pair."""
    user = await UserService.authenticate_user(
        db=db, email=login_data.email, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    user.last_login = func.now()
    await db.commit()

    return _issue_token_pair(user.email)


@router.post("/refresh", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh(
    request: Request,
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a fresh access + refresh pair."""
    decoded = verify_token(payload.refresh_token, expected_type="refresh")
    if decoded is None or decoded.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    email = decoded["sub"]
    user = (
        await db.execute(select(UserModel).where(UserModel.email == email))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid"
        )

    return _issue_token_pair(email)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user),
):
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService.update_user(
        db=db, user_id=current_user.id, user_update=user_update
    )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    success = await UserService.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_change.current_password,
        new_password=password_change.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password",
        )
    return {"message": "Password changed successfully"}


@router.post("/deactivate")
async def deactivate_account(
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await UserService.deactivate_user(db=db, user_id=current_user.id)
    return {"message": "Account deactivated successfully"}


@router.post("/verify-token")
async def verify_token_endpoint(
    current_user: UserModel = Depends(get_current_active_user),
):
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
    }
