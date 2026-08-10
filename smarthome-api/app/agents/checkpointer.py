import sqlite3
from pathlib import Path

from app.api.deps import SETTINGS_DEPENDENCY
from langgraph.checkpoint.sqlite import SqliteSaver

_connection: sqlite3.Connection | None = None
_saver: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    global _saver
    if _saver is None:
        database_url = SETTINGS_DEPENDENCY.database_url
        if database_url.startswith("sqlite:///./"):
            db_path = database_url.removeprefix("sqlite:///./")
        elif database_url.startswith("sqlite:///"):
            db_path = database_url.removeprefix("sqlite:///")
        else:
            raise RuntimeError("Agent checkpointer 仅支持 SQLite 数据库")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        global _connection
        _connection = sqlite3.connect(db_path, check_same_thread=False)
        _saver = SqliteSaver(_connection)
    return _saver


def init_checkpoiter() -> None:
    saver = get_checkpointer()
    saver.setup()
