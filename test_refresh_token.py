"""
Tests for security question and password recovery functionality
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from src.main import app
from src.core.database import get_db
from src.domain.auth.services import AuthService
from src.domain.auth.schemas import UserCreate


class TestSecurityQuestions:
    """Test class for security question functionality"""
    
    def setup_method(self):
        """Setup test data"""
        self.base_url = "/api/v1/auth"
        self.test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "security_question_id": 1,
            "security_answer": "fluffy"
        }
    
    @pytest.mark.asyncio
    async def test_get_security_questions(self):
        """Test getting security questions endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"{self.base_url}/security-questions")
            
            assert response.status_code == 200
            questions = response.json()
            assert isinstance(questions, list)
            assert len(questions) > 0
            
            # Check structure of first question
            question = questions[0]
            assert "id" in question
            assert "question" in question
            assert "is_active" in question
            assert "created_at" in question
    
    @pytest.mark.asyncio
    async def test_register_with_security_question(self):
        """Test user registration with security question"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First get available questions
            response = await client.get(f"{self.base_url}/security-questions")
            questions = response.json()
            
            # Use first available question
            user_data = self.test_user.copy()
            user_data["security_question_id"] = questions[0]["id"]
            
            response = await client.post(f"{self.base_url}/register", json=user_data)
            
            assert response.status_code == 201
            user = response.json()
            assert user["email"] == user_data["email"]
            assert user["username"] == user_data["username"]
            assert "id" in user
    
    @pytest.mark.asyncio
    async def test_register_with_invalid_security_question(self):
        """Test registration with invalid security question ID"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user_data = self.test_user.copy()
            user_data["security_question_id"] = 99999  # Invalid ID
            
            response = await client.post(f"{self.base_url}/register", json=user_data)
            
            assert response.status_code == 400
            assert "Invalid security question" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_flow(self):
        """Test complete forgot password flow"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First register a user
            response = await client.get(f"{self.base_url}/security-questions")
            questions = response.json()
            
            user_data = self.test_user.copy()
            user_data["security_question_id"] = questions[0]["id"]
            
            await client.post(f"{self.base_url}/register", json=user_data)
            
            # Test forgot password
            forgot_request = {"email": user_data["email"]}
            response = await client.post(f"{self.base_url}/forgot-password", json=forgot_request)
            
            assert response.status_code == 200
            security_response = response.json()
            assert "question" in security_response
            assert security_response["question"] == questions[0]["question"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            forgot_request = {"email": "nonexistent@example.com"}
            response = await client.post(f"{self.base_url}/forgot-password", json=forgot_request)
            
            assert response.status_code == 404
            assert "If this email exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test successful password reset"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register user
            response = await client.get(f"{self.base_url}/security-questions")
            questions = response.json()
            
            user_data = self.test_user.copy()
            user_data["security_question_id"] = questions[0]["id"]
            
            await client.post(f"{self.base_url}/register", json=user_data)
            
            # Reset password
            reset_request = {
                "email": user_data["email"],
                "security_answer": user_data["security_answer"],
                "new_password": "newpassword123"
            }
            
            response = await client.post(f"{self.base_url}/reset-password", json=reset_request)
            
            assert response.status_code == 200
            reset_response = response.json()
            assert "Password reset successfully" in reset_response["message"]
            
            # Test login with new password
            login_data = {
                "username": user_data["username"],
                "password": "newpassword123"
            }
            
            response = await client.post(f"{self.base_url}/login", json=login_data)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_reset_password_wrong_answer(self):
        """Test password reset with wrong security answer"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register user
            response = await client.get(f"{self.base_url}/security-questions")
            questions = response.json()
            
            user_data = self.test_user.copy()
            user_data["security_question_id"] = questions[0]["id"]
            
            await client.post(f"{self.base_url}/register", json=user_data)
            
            # Try reset with wrong answer
            reset_request = {
                "email": user_data["email"],
                "security_answer": "wronganswer",
                "new_password": "newpassword123"
            }
            
            response = await client.post(f"{self.base_url}/reset-password", json=reset_request)
            
            assert response.status_code == 400
            assert "Incorrect security answer" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_security_answer_normalization(self):
        """Test that security answers are case-insensitive and trimmed"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register user with lowercase answer
            response = await client.get(f"{self.base_url}/security-questions")
            questions = response.json()
            
            user_data = self.test_user.copy()
            user_data["security_question_id"] = questions[0]["id"]
            user_data["security_answer"] = "fluffy"  # lowercase
            
            await client.post(f"{self.base_url}/register", json=user_data)
            
            # Reset with uppercase and spaces
            reset_request = {
                "email": user_data["email"],
                "security_answer": "  FLUFFY  ",  # uppercase with spaces
                "new_password": "newpassword123"
            }
            
            response = await client.post(f"{self.base_url}/reset-password", json=reset_request)
            
            assert response.status_code == 200
            assert "Password reset successfully" in response.json()["message"]


class TestSecurityQuestionValidation:
    """Test validation for security question inputs"""
    
    @pytest.mark.asyncio
    async def test_empty_security_answer(self):
        """Test registration with empty security answer"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/security-questions")
            questions = response.json()
            
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "security_question_id": questions[0]["id"],
                "security_answer": ""  # Empty answer
            }
            
            response = await client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_long_security_answer(self):
        """Test registration with overly long security answer"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/security-questions")
            questions = response.json()
            
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "security_question_id": questions[0]["id"],
                "security_answer": "a" * 201  # Too long
            }
            
            response = await client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 422  # Validation error


def run_tests():
    """Run all tests"""
    print("Running Security Question Tests...")
    print("=" * 50)
    
    # Note: These tests require a test database setup
    # In a real project, you would use pytest with proper fixtures
    print("Tests require proper test setup with database fixtures")
    print("Use: pytest test_refresh_token.py")


if __name__ == "__main__":
    run_tests()