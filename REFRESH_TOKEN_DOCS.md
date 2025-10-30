# Security Questions and Password Recovery Documentation

## Overview

This FastAPI application now includes a comprehensive security question system for password recovery. Users must select a security question and provide an answer during registration, which can later be used to reset their password if forgotten.

## Features

### Security Questions
- Predefined list of 10 common security questions
- Questions are stored in the `security_questions` table
- Can be managed and extended by administrators
- Each question has an ID and active status

### User Registration
- Users must select a security question during registration
- Security answers are hashed and stored securely
- Same password hashing mechanism used for answers

### Password Recovery
- Two-step process: forgot password → security question → password reset
- Security answers are case-insensitive and trimmed
- All refresh tokens are revoked after successful password reset

## API Endpoints

### 1. Get Security Questions
```
GET /api/v1/auth/security-questions
```

**Response:**
```json
[
  {
    "id": 1,
    "question": "What was the name of your first pet?",
    "is_active": true,
    "created_at": "2023-10-30T10:00:00Z"
  },
  {
    "id": 2,
    "question": "What was the make of your first car?",
    "is_active": true,
    "created_at": "2023-10-30T10:00:00Z"
  }
]
```

### 2. User Registration (Updated)
```
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "security_question_id": 1,
  "security_answer": "fluffy"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2023-10-30T10:00:00Z",
  "updated_at": null
}
```

### 3. Forgot Password
```
POST /api/v1/auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "question": "What was the name of your first pet?"
}
```

### 4. Reset Password
```
POST /api/v1/auth/reset-password
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "security_answer": "fluffy",
  "new_password": "newsecurepassword123"
}
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

## Database Schema

### security_questions Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| question | String | The security question text |
| is_active | Boolean | Whether the question is active |
| created_at | DateTime | When the question was created |

### users Table (Updated)
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String | User email (unique) |
| username | String | Username (unique) |
| hashed_password | String | Hashed password |
| security_question_id | Integer | FK to security_questions |
| hashed_security_answer | String | Hashed security answer |
| is_active | Boolean | User active status |
| is_superuser | Boolean | Superuser status |
| created_at | DateTime | User creation time |
| updated_at | DateTime | Last update time |

## Default Security Questions

1. What was the name of your first pet?
2. What was the make of your first car?
3. What elementary school did you attend?
4. What is your mother's maiden name?
5. In what city were you born?
6. What is the name of your favorite teacher?
7. What was your childhood nickname?
8. What is the name of the street you grew up on?
9. What was your favorite food as a child?
10. What is your favorite movie?

## Security Considerations

### Answer Normalization
- Security answers are converted to lowercase
- Leading/trailing whitespace is removed
- This ensures consistent matching regardless of user input variations

### Password Reset Security
- All refresh tokens are revoked after successful password reset
- Forces re-authentication on all devices
- Prevents unauthorized access if account was compromised

### Email Validation
- Forgot password endpoint doesn't reveal if an email exists in the system
- Returns generic message for non-existent emails
- Prevents email enumeration attacks

## Migration

To add security questions to an existing database:

1. Run the migration script:
```bash
python migration_add_security_questions.py
```

2. This will:
   - Create the `security_questions` table
   - Add security question columns to the `users` table
   - Populate default security questions

## Error Handling

### Common Error Responses

**Invalid Security Question ID (400)**
```json
{
  "detail": "Invalid security question"
}
```

**Incorrect Security Answer (400)**
```json
{
  "detail": "Incorrect security answer"
}
```

**No Security Question Set (400)**
```json
{
  "detail": "No security question set for this account"
}
```

**User Not Found (404)**
```json
{
  "detail": "User not found"
}
```

## Testing

Use the `example_refresh_token_usage.py` script to test the complete flow:

```bash
python example_refresh_token_usage.py
```

This script demonstrates:
- Getting available security questions
- Registering users with security questions
- Password recovery process
- Password reset functionality
- Login with new password

## Future Enhancements

Potential improvements for the security question system:

1. **Multiple Security Questions**: Allow users to set multiple questions
2. **Custom Questions**: Allow users to create their own security questions
3. **Question History**: Track when questions were last used
4. **Account Lockout**: Implement lockout after multiple incorrect answers
5. **Admin Management**: Admin interface for managing security questions
6. **Backup Methods**: Additional recovery methods (phone, backup codes)
7. **Audit Logging**: Log all password reset attempts for security monitoring