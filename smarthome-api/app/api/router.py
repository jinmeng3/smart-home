from fastapi import APIRouter

from app.api.routes import (
    account,
    agent,
    ai_model,
    auth,
    automations,
    chat,
    device,
    households,
    members,
    overview,
    rooms,
    scenes,
)

api_router = APIRouter(prefix="/api")

                                    
api_router.include_router(account.router)
api_router.include_router(automations.router)
api_router.include_router(ai_model.router)
api_router.include_router(chat.router)
api_router.include_router(agent.router)
api_router.include_router(device.router)
api_router.include_router(households.router)
api_router.include_router(members.router)
api_router.include_router(overview.router)
api_router.include_router(rooms.router)
api_router.include_router(scenes.router)
api_router.include_router(auth.router)
