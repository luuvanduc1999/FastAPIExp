import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base, get_db
from src.main import app

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    """Test user data with security question"""
    # First, get available security questions
    response = client.get("/api/v1/auth/security-questions")
    questions = response.json()
    
    # If no questions exist, they will be created automatically
    if not questions:
        response = client.get("/api/v1/auth/security-questions")
        questions = response.json()
    
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
        "security_question_id": str(questions[0]["id"]),
        "security_answer": "test answer"
    }