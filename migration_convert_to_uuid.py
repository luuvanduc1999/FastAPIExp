"""
Database migration script to convert Integer IDs to UUIDs
WARNING: This will drop and recreate all auth tables. Backup your data first!
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.core.database import Base
from src.domain.auth.models import SecurityQuestion, User, RefreshToken
from src.domain.auth.repositories import SecurityQuestionRepository


async def run_migration():
    """Run the migration to convert IDs to UUIDs"""
    
    print("=" * 70)
    print("WARNING: This migration will DROP and RECREATE all auth tables!")
    print("All existing data will be LOST!")
    print("=" * 70)
    
    response = input("\nAre you sure you want to continue? Type 'YES' to proceed: ")
    if response != "YES":
        print("Migration cancelled.")
        return
    
    # Create async engine
    engine = create_async_engine(settings.ASYNC_DATABASE_URL or settings.DATABASE_URL)
    
    print("\nDropping existing tables...")
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating new tables with UUID columns...")
    # Create tables with UUID columns
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    print("Initializing default security questions...")
    async with async_session() as session:
        # Initialize default security questions
        security_question_repo = SecurityQuestionRepository(session)
        questions = await security_question_repo.create_default_questions()
        
        if questions:
            print(f"Created {len(questions)} default security questions")
            for q in questions:
                print(f"  - {q.id}: {q.question}")
        else:
            print("Security questions already exist")
    
    await engine.dispose()
    print("\n✓ Migration completed successfully!")
    print("\nNOTE: All IDs are now UUIDs. You may need to update any external references.")


if __name__ == "__main__":
    asyncio.run(run_migration())
