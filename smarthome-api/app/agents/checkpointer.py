import sqlite3
import threading
from pathlib import Path

from app.agents.errors import AgentCheckpointerError
from app.core.config import get_settings
from langgraph.checkpoint.sqlite import SqliteSaver

_connection: sqlite3.Connection | None = None
_saver: SqliteSaver | None = None

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None
_saver: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    global _saver, _connection
    if _saver is not None:
        return _saver
    with _lock:
        if _saver is not None:
            return _saver
        database_url = get_settings().database_url
        if database_url.startswith("sqlite:///./"):
            db_path = database_url.removeprefix("sqlite:///./")
        elif database_url.startswith("sqlite:///"):
            db_path = database_url.removeprefix("sqlite:///")
        else:
            raise AgentCheckpointerError("Agent checkpointer 仅支持 SQLite 数据库")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            _connection = sqlite3.connect(db_path, check_same_thread=False)
            _saver = SqliteSaver(_connection)
            _saver.setup()
        except Exception as exc:
            if _connection is not None:
                _connection.close()
                _connection = None
            raise AgentCheckpointerError(
                f"检查点初始化失败: {exc.__class__.__name__}"
            ) from exc
    return _saver


def init_checkpointer() -> None:
    get_checkpointer()


def close_checkpointer() -> None:
    global _saver, _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None
        _saver = None
