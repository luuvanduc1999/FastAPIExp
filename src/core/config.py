import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    ASYNC_DATABASE_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Auth App"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any] = None) -> Any:
        if isinstance(v, str):
            return v
        raise ValueError("DATABASE_URL must be provided")
    
    @field_validator("ASYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_connection(cls, v: Optional[str], values: Dict[str, Any] = None) -> Any:
        if v is not None:
            return v
        # If ASYNC_DATABASE_URL is not provided, derive it from DATABASE_URL
        if values and "DATABASE_URL" in values:
            db_url = values["DATABASE_URL"]
            if db_url.startswith("sqlite://"):
                return db_url.replace("sqlite://", "sqlite+aiosqlite://")
            elif db_url.startswith("postgresql://"):
                return db_url.replace("postgresql://", "postgresql+asyncpg://")
            elif db_url.startswith("mysql://"):
                return db_url.replace("mysql://", "mysql+aiomysql://")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()