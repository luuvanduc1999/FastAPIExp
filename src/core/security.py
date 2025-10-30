from datetime import datetime, timedelta
from typing import Any, Union
import hashlib
import secrets

from jose import jwt
from passlib.context import CryptContext

from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token() -> str:
    """Create a secure random refresh token"""
    return secrets.token_urlsafe(32)


def verify_token(token: str, token_type: str = "access") -> Union[str, None]:
    """Verify a JWT token and return the subject if valid"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type_from_payload: str = payload.get("type", "access")
        
        if username is None or token_type_from_payload != token_type:
            return None
            
        return username
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Apply the same pre-hashing logic for verification
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # bcrypt has a 72-byte limit, so we pre-hash long passwords with SHA-256
    if len(password.encode('utf-8')) > 72:
        # Use SHA-256 to reduce password to a fixed length
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password)