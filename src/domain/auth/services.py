from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.security import create_access_token
from src.domain.auth.repositories import UserRepository
from src.domain.auth.schemas import Token, User, UserCreate, UserLogin


class AuthService:
    """Service for authentication business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = self.user_repository.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Create new user
        db_user = self.user_repository.create(user_data)
        return User.model_validate(db_user)

    def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return access token"""
        user = self.user_repository.authenticate(
            login_data.username, login_data.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not self.user_repository.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db_user = self.user_repository.get_by_username(username)
        if db_user:
            return User.model_validate(db_user)
        return None

    def get_current_user(self, username: str) -> User:
        """Get current authenticated user"""
        user = self.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user