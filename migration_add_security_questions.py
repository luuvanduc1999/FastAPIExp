"""
Database migration script to add security questions functionality
Run this script to add the necessary tables and columns for security questions
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.core.database import Base
from src.domain.auth.models import SecurityQuestion, User
from src.domain.auth.repositories import SecurityQuestionRepository


async def run_migration():
    """Run the migration to add security questions"""
    
    # Create async engine
    engine = create_async_engine(settings.ASYNC_DATABASE_URL or settings.DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Initialize default security questions
        security_question_repo = SecurityQuestionRepository(session)
        questions = await security_question_repo.create_default_questions()
        
        if questions:
            print(f"Created {len(questions)} default security questions:")
            for q in questions:
                print(f"- {q.question}")
        else:
            print("Security questions already exist in the database")
    
    await engine.dispose()
    print("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())