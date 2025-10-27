from datetime import datetime
from typing import Optional

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
    is_active: Optional[bool] = True
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 200:
            raise ValueError('Password is too long (max 200 bytes)')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


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
    id: int
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
    token_type: str


class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None