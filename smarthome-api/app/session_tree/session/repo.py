"""会话仓库：创建 / 打开 / 列出 / 删除 / 分叉会话。"""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from app.session_tree.errors import SessionError
from app.session_tree.session.storage import InMemorySessionStorage, Session, now_ms
from app.session_tree.session.types import CreateOptions, ForkOptions, SessionMetadata

# 模块级别名：避免在定义 list 方法的类内部使用 list[...] 时与内置 list 冲突。
SessionMetadataList = list[SessionMetadata]


class SessionRepo(Protocol):
    def create(self, options: CreateOptions | None = None) -> Session: ...
    def open(self, metadata: SessionMetadata) -> Session: ...
    def list(self) -> SessionMetadataList: ...
    def find_metadata(self, session_key: str) -> SessionMetadata | None: ...
    def delete(self, metadata: SessionMetadata) -> None: ...
    def fork(
        self,
        source: SessionMetadata,
        options: ForkOptions,
        create_options: CreateOptions | None = None,
    ) -> Session: ...


class InMemorySessionRepo:
    def __init__(self) -> None:
        self._sessions: dict[str, InMemorySessionStorage] = {}

    def create(self, options: CreateOptions | None = None) -> Session:
        options = options or CreateOptions()
        session_key = options.session_key or uuid4().hex
        if session_key in self._sessions:
            raise SessionError("already_exists", f"Session already exists: {session_key}")
        storage = InMemorySessionStorage(
            SessionMetadata(
                session_key=session_key,
                parent_session_key=options.parent_session_key,
                created_at=now_ms(),
            )
        )
        self._sessions[session_key] = storage
        return Session(storage)

    def open(self, metadata: SessionMetadata) -> Session:
        return Session(self._require_storage(metadata.session_key))

    def list(self) -> SessionMetadataList:
        return [storage.get_metadata() for storage in self._sessions.values()]

    def find_metadata(self, session_key: str) -> SessionMetadata | None:
        storage = self._sessions.get(session_key)
        return storage.get_metadata() if storage is not None else None

    def delete(self, metadata: SessionMetadata) -> None:
        self._sessions.pop(metadata.session_key, None)

    def fork(
        self,
        source: SessionMetadata,
        options: ForkOptions,
        create_options: CreateOptions | None = None,
    ) -> Session:
        source_storage = self._require_storage(source.session_key)
        create_options = create_options or CreateOptions()
        session_key = create_options.session_key or uuid4().hex
        if session_key in self._sessions:
            raise SessionError("already_exists", f"Session already exists: {session_key}")
        metadata = SessionMetadata(
            session_key=session_key,
            parent_session_key=create_options.parent_session_key or source.session_key,
            created_at=now_ms(),
        )
        storage = source_storage.fork(metadata, options)
        self._sessions[session_key] = storage
        return Session(storage)

    def _require_storage(self, session_key: str) -> InMemorySessionStorage:
        storage = self._sessions.get(session_key)
        if storage is None:
            raise SessionError("not_found", f"Session not found: {session_key}")
        return storage
