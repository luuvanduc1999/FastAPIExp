from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.domain.auth.schemas import (
    Token, 
    TokenData, 
    User, 
    UserCreate, 
    UserLogin,
    TokenRefresh,
    TokenExtend,
    TokenExtendResponse,
    AccessTokenResponse,
    SecurityQuestion,
    ForgotPasswordRequest,
    SecurityQuestionResponse,
    PasswordResetRequest,
    PasswordResetResponse
)
from src.domain.auth.services import AuthService

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token"""
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(login_data)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(token_refresh: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(token_refresh)


@router.post("/extend-token", response_model=TokenExtendResponse)
async def extend_refresh_token(token_extend: TokenExtend, db: AsyncSession = Depends(get_db)):
    """Extend refresh token expiry date"""
    auth_service = AuthService(db)
    success = await auth_service.extend_refresh_token(
        token_extend.refresh_token, 
        token_extend.extend_days
    )
    return TokenExtendResponse(
        message="Refresh token extended successfully" if success else "Failed to extend token",
        success=success
    )


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.get("/security-questions", response_model=List[SecurityQuestion])
async def get_security_questions(db: AsyncSession = Depends(get_db)):
    """Get all available security questions"""
    auth_service = AuthService(db)
    questions = await auth_service.get_security_questions()
    if not questions:
        # Initialize default questions if none exist
        questions = await auth_service.initialize_security_questions()
    return questions


@router.post("/forgot-password", response_model=SecurityQuestionResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Get security question for password recovery"""
    auth_service = AuthService(db)
    return await auth_service.forgot_password(request)


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using security question answer"""
    auth_service = AuthService(db)
    return await auth_service.reset_password(request)