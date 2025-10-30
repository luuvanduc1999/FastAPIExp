from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# Base schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


# Request schemas
class UserCreate(BaseModel):
    """Schema for creating a regular user (cannot set superuser status)"""
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8, max_length=200)
    security_question_id: UUID
    security_answer: str = Field(..., min_length=1, max_length=200)
    is_active: Optional[bool] = True
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Password is too long (max 200 bytes)')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('security_answer')
    def validate_security_answer(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Security answer is too long (max 200 bytes)')
        if len(v) < 1:
            raise ValueError('Security answer cannot be empty')
        return v.strip().lower()  # Normalize answer for comparison


class SuperUserCreate(UserBase):
    """Schema for creating a superuser (only accessible by existing superusers)"""
    password: str = Field(..., min_length=8, max_length=200)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Password is too long (max 200 bytes)')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str = Field(..., max_length=200)

# Response schemas
class User(UserBase):
    """Schema for user response"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    """Schema for user in database (includes hashed password)"""
    hashed_password: str

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Schema for access token only response"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None


class RefreshTokenBase(BaseModel):
    """Base refresh token schema"""
    token: str
    expires_at: datetime
    is_revoked: bool = False


class RefreshTokenCreate(RefreshTokenBase):
    """Schema for creating refresh token"""
    user_id: UUID


class RefreshToken(RefreshTokenBase):
    """Schema for refresh token response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Security Question schemas
class SecurityQuestionBase(BaseModel):
    """Base security question schema"""
    question: str
    is_active: bool = True


class SecurityQuestion(SecurityQuestionBase):
    """Schema for security question response"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityQuestionCreate(SecurityQuestionBase):
    """Schema for creating security question"""
    pass


# Password Recovery schemas
class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class SecurityQuestionResponse(BaseModel):
    """Schema for security question response during password recovery"""
    question: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr
    security_answer: str = Field(..., min_length=1, max_length=200)
    new_password: str = Field(..., min_length=8, max_length=200)
    
    @validator('security_answer')
    def validate_security_answer(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Security answer is too long (max 200 bytes)')
        if len(v) < 1:
            raise ValueError('Security answer cannot be empty')
        return v.strip().lower()  # Normalize answer for comparison
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Password is too long (max 200 bytes)')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class PasswordResetResponse(BaseModel):
    """Schema for password reset response"""
    message: str