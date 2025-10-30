"""
Example usage of the security question and password recovery functionality
"""

import asyncio
import httpx


async def example_security_question_flow():
    """Example of using security questions for password recovery"""
    
    base_url = "http://localhost:8000/api/v1/auth"
    
    async with httpx.AsyncClient() as client:
        
        # 1. Get available security questions
        print("1. Getting available security questions...")
        response = await client.get(f"{base_url}/security-questions")
        security_questions = response.json()
        print(f"Available questions: {len(security_questions)} found")
        for q in security_questions:
            print(f"  - ID {q['id']}: {q['question']}")
        
        # 2. Register a new user with security question
        print("\n2. Registering a new user with security question...")
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepassword123",
            "security_question_id": security_questions[0]["id"],  # Use first question
            "security_answer": "fluffy"  # Answer to "What was the name of your first pet?"
        }
        
        response = await client.post(f"{base_url}/register", json=user_data)
        if response.status_code == 201:
            user = response.json()
            print(f"User registered successfully: {user['username']} ({user['email']})")
        else:
            print(f"Registration failed: {response.json()}")
            return
        
        # 3. Simulate forgot password
        print("\n3. Initiating forgot password process...")
        forgot_request = {
            "email": "test@example.com"
        }
        
        response = await client.post(f"{base_url}/forgot-password", json=forgot_request)
        if response.status_code == 200:
            security_response = response.json()
            print(f"Security question: {security_response['question']}")
        else:
            print(f"Forgot password failed: {response.json()}")
            return
        
        # 4. Reset password with security answer
        print("\n4. Resetting password with security answer...")
        reset_request = {
            "email": "test@example.com",
            "security_answer": "fluffy",  # Correct answer
            "new_password": "newsecurepassword123"
        }
        
        response = await client.post(f"{base_url}/reset-password", json=reset_request)
        if response.status_code == 200:
            reset_response = response.json()
            print(f"Password reset successful: {reset_response['message']}")
        else:
            print(f"Password reset failed: {response.json()}")
            return
        
        # 5. Test login with new password
        print("\n5. Testing login with new password...")
        login_data = {
            "username": "testuser",
            "password": "newsecurepassword123"
        }
        
        response = await client.post(f"{base_url}/login", json=login_data)
        if response.status_code == 200:
            token_response = response.json()
            print("Login successful with new password!")
            print(f"Access token received: {token_response['access_token'][:20]}...")
        else:
            print(f"Login failed: {response.json()}")


async def example_registration_with_security_question():
    """Example of registering with different security questions"""
    
    base_url = "http://localhost:8000/api/v1/auth"
    
    async with httpx.AsyncClient() as client:
        
        # Get security questions
        response = await client.get(f"{base_url}/security-questions")
        questions = response.json()
        
        # Example users with different security questions
        users = [
            {
                "email": "alice@example.com",
                "username": "alice",
                "password": "alicepassword123",
                "security_question_id": questions[0]["id"],
                "security_answer": "buddy"
            },
            {
                "email": "bob@example.com", 
                "username": "bob",
                "password": "bobpassword123",
                "security_question_id": questions[1]["id"],  # Different question
                "security_answer": "honda civic"
            },
            {
                "email": "charlie@example.com",
                "username": "charlie", 
                "password": "charliepassword123",
                "security_question_id": questions[2]["id"],  # Another question
                "security_answer": "lincoln elementary"
            }
        ]
        
        for user_data in users:
            response = await client.post(f"{base_url}/register", json=user_data)
            if response.status_code == 201:
                user = response.json()
                question = next(q for q in questions if q["id"] == user_data["security_question_id"])
                print(f"Registered {user['username']} with question: '{question['question']}'")
            else:
                print(f"Failed to register {user_data['username']}: {response.json()}")


if __name__ == "__main__":
    print("Security Question Example Usage")
    print("================================")
    
    print("\nExample 1: Complete password recovery flow")
    asyncio.run(example_security_question_flow())
    
    print("\n\nExample 2: Registration with different security questions") 
    asyncio.run(example_registration_with_security_question())