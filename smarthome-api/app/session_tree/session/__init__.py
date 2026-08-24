"""会话树存储核心：类型、状态机、门面、内存 / SQLite 实现、上下文投影。"""

from app.session_tree.session.context import build_session_context
from app.session_tree.session.repo import InMemorySessionRepo, SessionRepo
from app.session_tree.session.sqlite import SqliteSessionRepo, SqliteSessionStorage
from app.session_tree.session.state import SessionState
from app.session_tree.session.storage import (
    InMemorySessionStorage,
    Session,
    SessionStorage,
)
from app.session_tree.session.types import (
    CompactionSettings,
    CreateOptions,
    Entry,
    EntryQuery,
    ForkOptions,
    LanePointer,
    LogItem,
    Record,
    RecordQuery,
    SessionMetadata,
    SessionStats,
)

__all__ = [
    "CompactionSettings",
    "CreateOptions",
    "Entry",
    "EntryQuery",
    "ForkOptions",
    "InMemorySessionRepo",
    "InMemorySessionStorage",
    "LanePointer",
    "LogItem",
    "Record",
    "RecordQuery",
    "Session",
    "SessionMetadata",
    "SessionRepo",
    "SessionState",
    "SessionStats",
    "SessionStorage",
    "SqliteSessionRepo",
    "SqliteSessionStorage",
    "build_session_context",
]
