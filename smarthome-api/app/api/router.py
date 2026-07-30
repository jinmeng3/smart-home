from fastapi import APIRouter

from app.api.routes import account, ai_model, households, members

api_router = APIRouter(prefix="/api")
api_router.include_router(account.router)
api_router.include_router(ai_model.router)
api_router.include_router(households.router)
api_router.include_router(members.router)
