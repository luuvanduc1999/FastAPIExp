from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.config import settings

# Sync engine for migrations and initial setup
engine = create_engine(settings.DATABASE_URL)

# Async engine for application use  
async_database_url = settings.ASYNC_DATABASE_URL or settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
async_engine = create_async_engine(async_database_url)

# Sync session for migrations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async session for application
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

Base = declarative_base()


def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get sync database session (for migrations)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        yield session


# Alias for backward compatibility and cleaner imports
get_db = get_async_db