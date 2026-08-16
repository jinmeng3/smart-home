import asyncio
from pathlib import Path

import aiosqlite
from app.agents.errors import AgentCheckpointerError
from app.core.config import Settings, get_settings
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_lock = asyncio.Lock()
_saver: BaseCheckpointSaver | None = None
_sqlite_connection: aiosqlite.Connection | None = None


async def get_checkpointer() -> BaseCheckpointSaver:
    global _saver
    if _saver is not None:
        return _saver

    async with _lock:
        if _saver is not None:
            return _saver

        _saver = await _create_sqlite_checkpointer(get_settings())
        return _saver


def _sqlite_path(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite:///"):
        return database_url.removeprefix("sqlite+aiosqlite:///")
    if database_url.startswith("sqlite:///./"):
        return database_url.removeprefix("sqlite:///./")
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    return "db/agent_checkpoints.db"


async def _create_sqlite_checkpointer(settings: Settings) -> AsyncSqliteSaver:
    """创建单实例开发环境使用的 SQLite checkpointer。"""
    global _sqlite_connection

    db_path = _sqlite_path(settings.checkpointer_database_url or settings.database_url)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn: aiosqlite.Connection | None = None

    try:
        conn = await aiosqlite.connect(db_path)
        saver = AsyncSqliteSaver(conn)
        await saver.setup()
        _sqlite_connection = conn
        return saver
    except Exception as exc:
        if conn is not None:
            await conn.close()
        raise AgentCheckpointerError(
            f"SQLite checkpointer 初始化失败: {exc.__class__.__name__}"
        ) from exc


async def init_checkpointer() -> None:
    await get_checkpointer()


async def close_checkpointer() -> None:
    global _saver, _sqlite_connection

    async with _lock:
        sqlite_connection = _sqlite_connection
        _saver = None
        _sqlite_connection = None

    if sqlite_connection is not None:
        await sqlite_connection.close()
