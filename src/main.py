from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import api_router
from src.core.config import settings
from src.core.database import create_tables

# Import all models to ensure they are registered with Base.metadata
from src.domain.auth.models import SecurityQuestion, User, RefreshToken

# Create database tables on startup
create_tables()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI application with authentication",
    version="1.0.0",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI Auth App"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}