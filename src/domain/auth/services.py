from datetime import timedelta, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import create_access_token, create_refresh_token
from src.domain.auth.repositories import UserRepository, RefreshTokenRepository, SecurityQuestionRepository
from src.domain.auth.schemas import (
    Token, 
    User, 
    UserCreate, 
    UserLogin, 
    RefreshTokenCreate,
    AccessTokenResponse,
    TokenRefresh,
    SecurityQuestion,
    ForgotPasswordRequest,
    SecurityQuestionResponse,
    PasswordResetRequest,
    PasswordResetResponse
)


class AuthService:
    """Service for authentication business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.refresh_token_repository = RefreshTokenRepository(db)
        self.security_question_repository = SecurityQuestionRepository(db)

    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await self.user_repository.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Validate security question exists
        security_question = await self.security_question_repository.get_by_id(user_data.security_question_id)
        if not security_question or not security_question.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid security question"
            )

        # Create new user
        db_user = await self.user_repository.create(user_data)
        return User.model_validate(db_user)

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return access and refresh tokens"""
        user = await self.user_repository.authenticate(
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

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )

        # Create refresh token
        refresh_token_value = create_refresh_token()
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_token_data = RefreshTokenCreate(
            token=refresh_token_value,
            user_id=user.id,
            expires_at=refresh_token_expires,
            is_revoked=False
        )
        
        await self.refresh_token_repository.create(refresh_token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer"
        )

    async def refresh_access_token(self, token_refresh: TokenRefresh) -> AccessTokenResponse:
        """Refresh access token using refresh token"""
        # Get refresh token from database
        refresh_token = await self.refresh_token_repository.get_by_token(token_refresh.refresh_token)
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is valid
        if not self.refresh_token_repository.is_valid(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )
        
        # Get user
        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if not user or not self.user_repository.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Always extend refresh token when refreshing access token (sliding expiration)
        await self.refresh_token_repository.extend_token_expiry(token_refresh.refresh_token)
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        return AccessTokenResponse(
            access_token=access_token,
            token_type="bearer"
        )

    async def extend_refresh_token(self, token: str, extend_days: int = None) -> bool:
        """Manually extend refresh token expiry"""
        # Get refresh token from database
        refresh_token = await self.refresh_token_repository.get_by_token(token)
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is valid
        if not self.refresh_token_repository.is_valid(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )
        
        # Extend the token
        return await self.refresh_token_repository.extend_token_expiry(token, extend_days)

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a specific refresh token"""
        return await self.refresh_token_repository.revoke_token(token)

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user"""
        return await self.refresh_token_repository.revoke_all_user_tokens(user_id)

    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        return await self.revoke_refresh_token(refresh_token)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db_user = await self.user_repository.get_by_username(username)
        if db_user:
            return User.model_validate(db_user)
        return None

    async def get_current_user(self, username: str) -> User:
        """Get current authenticated user"""
        user = await self.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_current_user_by_email(self, email: str) -> User:
        """Get current authenticated user by email"""
        db_user = await self.user_repository.get_by_email(email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return User.model_validate(db_user)

    async def get_security_questions(self) -> List[SecurityQuestion]:
        """Get all active security questions"""
        questions = await self.security_question_repository.get_all_active()
        return [SecurityQuestion.model_validate(q) for q in questions]

    async def initialize_security_questions(self) -> List[SecurityQuestion]:
        """Initialize default security questions if none exist"""
        questions = await self.security_question_repository.create_default_questions()
        return [SecurityQuestion.model_validate(q) for q in questions]

    async def forgot_password(self, request: ForgotPasswordRequest) -> SecurityQuestionResponse:
        """Get security question for password recovery"""
        user = await self.user_repository.get_by_email(request.email)
        if not user:
            # Don't reveal that email doesn't exist for security reasons
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="If this email exists, you will receive password recovery information"
            )

        if not user.security_question or not user.hashed_security_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No security question set for this account"
            )

        return SecurityQuestionResponse(question=user.security_question.question)

    async def reset_password(self, request: PasswordResetRequest) -> PasswordResetResponse:
        """Reset password using security question answer"""
        user = await self.user_repository.get_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.security_question or not user.hashed_security_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No security question set for this account"
            )

        # Verify security answer
        if not await self.user_repository.verify_security_answer(user, request.security_answer):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect security answer"
            )

        # Update password
        success = await self.user_repository.update_password(user.id, request.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        # Revoke all refresh tokens for security
        await self.revoke_all_user_tokens(user.id)

        return PasswordResetResponse(message="Password reset successfully")