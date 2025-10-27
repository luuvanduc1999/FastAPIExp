# FastAPI Authentication App

A FastAPI application with authentication using SQLAlchemy, PostgreSQL, Poetry, Pytest, and Pydantic. Containerized with Docker.

## Features

- User authentication with JWT tokens
- Password hashing with bcrypt
- PostgreSQL database with SQLAlchemy ORM
- Domain-driven design structure
- RESTful API endpoints
- Comprehensive test coverage with Pytest
- Docker containerization
- pgAdmin for database management

## Project Structure

```
src/
├── domain/
│   └── auth/
│       ├── models.py          # Domain models
│       ├── schemas.py         # Pydantic schemas
│       ├── services.py        # Business logic
│       └── repositories.py    # Data access layer
├── api/
│   └── v1/
│       ├── auth.py           # Authentication endpoints
│       └── __init__.py
├── core/
│   ├── config.py             # Configuration
│   ├── database.py           # Database setup
│   ├── security.py           # Security utilities
│   └── __init__.py
└── main.py                   # Application entry point
```

## Quick Start with Docker

1. Clone the repository and navigate to the project directory

2. Start the application with Docker:
```bash
docker-compose up --build
```

3. Access the application:
- **API**: http://localhost:8000
- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)

## API Endpoints

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login user and get access token
- `GET /api/v1/auth/me` - Get current user profile (requires authentication)

## Development Setup (Without Docker)

1. Install Poetry (if not already installed):
```bash
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

2. Install dependencies:
```bash
poetry install
```

3. Set up PostgreSQL database and update `.env` file

4. Start the application:
```bash
poetry run uvicorn src.main:app --reload
```

## Testing

Run tests with:
```bash
poetry run pytest
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## Docker Services

- **web**: FastAPI application (port 8000)
- **db**: PostgreSQL database (port 5432)
- **pgadmin**: pgAdmin database management tool (port 5050)

## Usage Examples

### Register a new user
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "password123"
     }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "password123"
     }'
```

### Get current user (with token)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```