from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel

from src.api.v1.auth import get_current_user
from src.domain.auth.schemas import User

router = APIRouter()
security = HTTPBearer(auto_error=False)  # auto_error=False allows optional authentication


class GreetingResponse(BaseModel):
    """Schema for greeting response"""
    message: str
    user: Optional[User] = None
    is_authenticated: bool


class PublicGreetingResponse(BaseModel):
    """Schema for public greeting response"""
    message: str
    is_authenticated: bool
    login_hint: str


@router.get("/greeting", response_model=GreetingResponse)
async def get_greeting(current_user: User = Depends(get_current_user)):
    """
    Get a personalized greeting message for the authenticated user.
    
    This endpoint requires authentication and returns a greeting message
    with the current user's information.
    """
    greeting_message = f"Xin chào {current_user.username}! Chào mừng bạn đến với ứng dụng FastAPI!"
    
    return GreetingResponse(
        message=greeting_message,
        user=current_user,
        is_authenticated=True
    )


@router.get("/public-greeting", response_model=PublicGreetingResponse)
def get_public_greeting():
    """
    Get a public greeting message for anyone (no authentication required).
    
    This endpoint is accessible to everyone and provides information
    about how to access authenticated features.
    """
    return PublicGreetingResponse(
        message="Xin chào! Chào mừng bạn đến với ứng dụng FastAPI!",
        is_authenticated=False,
        login_hint="Vui lòng đăng nhập để nhận được lời chào cá nhân hóa tại /api/v1/home/greeting"
    )


@router.get("/smart-greeting")
async def get_smart_greeting(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Smart greeting that adapts based on authentication status.
    
    Returns personalized greeting if authenticated, generic greeting if not.
    This endpoint works for both authenticated and unauthenticated users.
    """
    if not credentials:
        return {
            "message": "Xin chào khách! Chào mừng bạn đến với ứng dụng FastAPI!",
            "is_authenticated": False,
            "suggestion": "Đăng ký hoặc đăng nhập để trải nghiệm đầy đủ tính năng",
            "login_endpoint": "/api/v1/auth/login",
            "register_endpoint": "/api/v1/auth/register"
        }
    
    try:
        # Try to get current user
        from src.core.database import get_db
        from src.core.config import settings
        from jose import JWTError, jwt
        from src.domain.auth.services import AuthService
        
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise JWTError("Invalid token")
        
        # Get database session and user
        async for db in get_db():
            auth_service = AuthService(db)
            user = await auth_service.get_current_user(username=username)
            
            if user is None:
                raise JWTError("User not found")
            
            return {
                "message": f"Xin chào {user.username}! Chào mừng bạn quay trở lại!",
                "is_authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "status": "Bạn đã đăng nhập thành công"
            }
        
    except (JWTError, Exception):
        return {
            "message": "Xin chào! Token không hợp lệ hoặc đã hết hạn.",
            "is_authenticated": False,
            "suggestion": "Vui lòng đăng nhập lại để tiếp tục",
            "login_endpoint": "/api/v1/auth/login"
        }


@router.get("/welcome")
async def get_welcome_message(current_user: User = Depends(get_current_user)):
    """
    Get a simple welcome message for authenticated users.
    
    Returns a simple JSON response with a welcome message.
    """
    return {
        "message": f"Chào mừng {current_user.username}!",
        "status": "authenticated",
        "user_id": current_user.id,
        "email": current_user.email
    }
