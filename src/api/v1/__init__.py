from fastapi import APIRouter

from src.api.v1 import auth, home

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(home.router, prefix="/home", tags=["home"])