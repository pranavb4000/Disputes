from fastapi import APIRouter

from app.api.v1 import auth, health, home

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(home.router)  # keep last: it owns the /{module_code}/... pattern
