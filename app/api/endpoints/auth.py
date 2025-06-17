from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.schemas.user import (
    UserCreate, User, LoginRequest, Token, 
    UserUpdate, PasswordChange
)
from app.services.user_service import UserService
from app.utils.deps import get_current_active_user
from app.models.user import User as UserModel

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    user = UserService.create_user(db=db, user_create=user_create)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    user = UserService.authenticate_user(
        db=db, 
        email=login_data.email, 
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    # Update last login
    from sqlalchemy.sql import func
    user.last_login = func.now()
    db.commit()
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=User)
def update_current_user(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    updated_user = UserService.update_user(
        db=db, 
        user_id=current_user.id, 
        user_update=user_update
    )
    return updated_user


@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    success = UserService.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_change.current_password,
        new_password=password_change.new_password
    )
    
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )


@router.post("/deactivate")
def deactivate_account(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user account"""
    UserService.deactivate_user(db=db, user_id=current_user.id)
    return {"message": "Account deactivated successfully"}


@router.post("/verify-token")
def verify_token(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Verify if token is valid"""
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email
    }
    