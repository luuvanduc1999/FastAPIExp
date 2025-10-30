from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.core.security import get_password_hash, verify_password
from src.domain.auth.models import User, RefreshToken, SecurityQuestion
from src.domain.auth.schemas import UserCreate, RefreshTokenCreate, SecurityQuestionCreate
from src.core.config import settings


class UserRepository:
    """Repository for user data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with security question"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.security_question))
            .filter(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_data.password)
        hashed_security_answer = get_password_hash(user_data.security_answer)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            security_question_id=user_data.security_question_id,
            hashed_security_answer=hashed_security_answer,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """Update user password"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def verify_security_answer(self, user: User, answer: str) -> bool:
        """Verify security question answer"""
        if not user.hashed_security_answer:
            return False
        return verify_password(answer, user.hashed_security_answer)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active"""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser"""
        return user.is_superuser

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def verify_security_answer(self, user: User, answer: str) -> bool:
        """Verify security question answer"""
        if not user.hashed_security_answer:
            return False
        return verify_password(answer, user.hashed_security_answer)


class SecurityQuestionRepository:
    """Repository for security question data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active(self) -> List[SecurityQuestion]:
        """Get all active security questions"""
        result = await self.db.execute(
            select(SecurityQuestion).filter(SecurityQuestion.is_active.is_(True))
        )
        return result.scalars().all()

    async def get_by_id(self, question_id: UUID) -> Optional[SecurityQuestion]:
        """Get security question by ID"""
        result = await self.db.execute(
            select(SecurityQuestion).filter(SecurityQuestion.id == question_id)
        )
        return result.scalar_one_or_none()

    async def create(self, question_data: SecurityQuestionCreate) -> SecurityQuestion:
        """Create a new security question"""
        db_question = SecurityQuestion(
            question=question_data.question,
            is_active=question_data.is_active,
        )
        self.db.add(db_question)
        await self.db.commit()
        await self.db.refresh(db_question)
        return db_question

    async def create_default_questions(self) -> List[SecurityQuestion]:
        """Create default security questions if none exist"""
        existing_count = await self.db.execute(select(SecurityQuestion))
        if existing_count.scalars().first() is not None:
            return []

        default_questions = [
            "What was the name of your first pet?",
            "What was the make of your first car?",
            "What elementary school did you attend?",
            "What is your mother's maiden name?",
            "In what city were you born?",
            "What is the name of your favorite teacher?",
            "What was your childhood nickname?",
            "What is the name of the street you grew up on?",
            "What was your favorite food as a child?",
            "What is your favorite movie?"
        ]

        created_questions = []
        for question_text in default_questions:
            question_data = SecurityQuestionCreate(
                question=question_text,
                is_active=True
            )
            db_question = await self.create(question_data)
            created_questions.append(db_question)

        return created_questions


class RefreshTokenRepository:
    """Repository for refresh token data access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, refresh_token_data: RefreshTokenCreate) -> RefreshToken:
        """Create a new refresh token"""
        db_refresh_token = RefreshToken(
            token=refresh_token_data.token,
            user_id=refresh_token_data.user_id,
            expires_at=refresh_token_data.expires_at,
            is_revoked=refresh_token_data.is_revoked,
        )
        self.db.add(db_refresh_token)
        await self.db.commit()
        await self.db.refresh(db_refresh_token)
        return db_refresh_token

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string"""
        result = await self.db.execute(
            select(RefreshToken).filter(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> List[RefreshToken]:
        """Get all refresh tokens for a user"""
        result = await self.db.execute(
            select(RefreshToken).filter(RefreshToken.user_id == user_id)
        )
        return result.scalars().all()

    async def revoke_token(self, token: str) -> bool:
        """Revoke a refresh token"""
        refresh_token = await self.get_by_token(token)
        if not refresh_token:
            return False
        
        refresh_token.is_revoked = True
        refresh_token.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user"""
        tokens = await self.get_by_user_id(user_id)
        revoked_count = 0
        
        for token in tokens:
            if not token.is_revoked:
                token.is_revoked = True
                token.updated_at = datetime.utcnow()
                revoked_count += 1
        
        await self.db.commit()
        return revoked_count

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from database"""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(RefreshToken).filter(RefreshToken.expires_at < now)
        )
        expired_tokens = result.scalars().all()
        
        for token in expired_tokens:
            await self.db.delete(token)
        
        await self.db.commit()
        return len(expired_tokens)

    def is_valid(self, refresh_token: RefreshToken) -> bool:
        """Check if refresh token is valid (not revoked and not expired)"""
        if refresh_token.is_revoked:
            return False
        
        if refresh_token.expires_at < datetime.utcnow():
            return False
        
        return True

    async def extend_token_expiry(self, token: str, extend_days: int = None) -> bool:
        """Extend refresh token expiry date"""
        if extend_days is None:
            extend_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
            
        refresh_token = await self.get_by_token(token)
        if not refresh_token or refresh_token.is_revoked:
            return False
        
        # Extend the expiry date
        refresh_token.expires_at = datetime.utcnow() + timedelta(days=extend_days)
        refresh_token.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    def should_extend_token(self, refresh_token: RefreshToken, threshold_days: int = 7) -> bool:
        """Check if token should be extended (when it's close to expiry)"""
        time_until_expiry = refresh_token.expires_at - datetime.utcnow()
        return time_until_expiry.days <= threshold_days