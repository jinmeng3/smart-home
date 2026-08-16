from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agents.checkpointer import close_checkpointer, init_checkpointer
from app.api.exceptions import register_exception_handlers
from app.api.router import api_router
from app.core.config import get_settings
from app.db.init_db import create_tables

settings = get_settings()
Path("db").mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
settings.avatar_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    await init_checkpointer()
    try:
        yield
    finally:
        await close_checkpointer()


app = FastAPI(lifespan=lifespan, title=settings.app_name)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
