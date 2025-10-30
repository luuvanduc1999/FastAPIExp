from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey, Text
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from src.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type stored as CHAR(36).
    Stores GUIDs as stringified hex values in all databases.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, GUID.GUID):
            return str(GUID.GUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, GUID.GUID):
            return GUID.GUID(value)
        return value


class SecurityQuestion(Base):
    """Security question model"""
    __tablename__ = "security_questions"

    id = Column(GUID(), primary_key=True, default=GUID.GUID4, index=True)
    question = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SecurityQuestion(id={self.id}, question='{self.question}')>"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=GUID.GUID4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    security_question_id = Column(GUID(), ForeignKey("security_questions.id"), nullable=True)
    hashed_security_answer = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    security_question = relationship("SecurityQuestion")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class RefreshToken(Base):
    """Refresh token model"""
    __tablename__ = "refresh_tokens"

    id = Column(GUID(), primary_key=True, default=GUID.GUID4, index=True)
    token = Column(Text, unique=True, index=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"