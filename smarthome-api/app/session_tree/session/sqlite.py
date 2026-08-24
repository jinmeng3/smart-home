"""SQLite 持久化实现（基于 SQLAlchemy）。

与内存实现共享同一 ``SessionState`` 与同一套不变式：每条写操作先落库
（append-only 的 mutation 行）再应用到内存，加载时按 ``seq`` 顺序重放。
"""

from __future__ import annotations

import copy
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as OrmSession

from app.models.session_tree import SessionTreeMutation, SessionTreeSession
from app.session_tree.errors import SessionError
from app.session_tree.session.codec import mutation_from_dict, mutation_to_dict
from app.session_tree.session.state import SessionState
from app.session_tree.session.storage import Session, now_ms
from app.session_tree.session.types import (
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

# 模块级别名：避免在定义 list 方法的类内部使用 list[...] 时与内置 list 冲突。
SessionMetadataList = list[SessionMetadata]


def _mutation_seq(mutation: dict[str, Any]) -> int:
    if mutation["kind"] == "entry":
        return mutation["entry"].seq
    if mutation["kind"] == "record":
        return mutation["record"].seq
    return mutation["seq"]


class SqliteSessionStorage:
    def __init__(self, db: OrmSession, session_id: int, metadata: SessionMetadata) -> None:
        self._db = db
        self._session_id = session_id
        self._metadata = copy.deepcopy(metadata)
        self._state = SessionState()
        self._load()

    # ---- loading ----

    def _load(self) -> None:
        rows = self._db.scalars(
            select(SessionTreeMutation)
            .where(SessionTreeMutation.session_id == self._session_id)
            .order_by(SessionTreeMutation.seq.asc())
        ).all()
        for row in rows:
            self._state.apply_mutation(mutation_from_dict(row.payload))

    # ---- persistence ----

    def _persist(self, mutation: dict[str, Any]) -> None:
        """写入 mutation 行但不提交、不应用（用于 fork 的批量写入）。"""
        self._db.add(
            SessionTreeMutation(
                session_id=self._session_id,
                seq=_mutation_seq(mutation),
                kind=mutation["kind"],
                payload=mutation_to_dict(mutation),
                created_at=now_ms(),
            )
        )
        self._db.flush()

    def _append_mutation(self, mutation: dict[str, Any]) -> None:
        """先持久化、后应用内存。"""
        self._persist(mutation)
        self._db.commit()
        self._state.apply_mutation(mutation)

    # ---- SessionStorage ----

    def get_metadata(self) -> SessionMetadata:
        return copy.deepcopy(self._metadata)

    def get_lanes(self) -> list[LanePointer]:
        return self._state.get_lanes()

    def create_lane(self, lane: str, at: str | None) -> None:
        self._state.validate_new_lane(lane)
        self._state.validate_target(at)
        self._append_mutation(
            {"kind": "lane", "seq": self._state.next_sequence, "lane": lane, "leaf_id": at}
        )

    def move_lane(self, lane: str, to: str | None) -> None:
        self._state.require_lane(lane)
        self._state.validate_target(to)
        self._append_mutation(
            {"kind": "lane", "seq": self._state.next_sequence, "lane": lane, "leaf_id": to}
        )

    def append_entry(self, entry: Entry, lane: str) -> Entry:
        parent_id = self._state.require_lane(lane)
        self._state.validate_unused_id(entry.id)
        entry.parent_id = parent_id
        entry.seq = self._state.next_sequence
        entry.timestamp = now_ms()
        self._append_mutation({"kind": "entry", "lane": lane, "entry": entry})
        return copy.deepcopy(entry)

    def append_record(self, record: Record) -> Record:
        self._state.require_lane(record.lane)
        self._state.validate_unused_id(record.id)
        if record.type == "operation_started":
            open_ops = self._state.find_open_operations(record.lane, 1)
            if open_ops:
                raise SessionError(
                    "storage",
                    f"Lane {record.lane} already has an open operation {open_ops[0].id}",
                )
        record.seq = self._state.next_sequence
        record.timestamp = now_ms()
        self._append_mutation({"kind": "record", "record": record})
        return copy.deepcopy(record)

    def get_entry(self, entry_id: str) -> Entry | None:
        entry = self._state.get_entry(entry_id)
        return copy.deepcopy(entry) if entry is not None else None

    def find_entries(self, query: EntryQuery | None = None) -> list[Entry]:
        return copy.deepcopy(self._state.find_entries(query))

    def find_entries_on_branch(self, query: EntryQuery) -> list[Entry]:
        return copy.deepcopy(self._state.find_entries_on_branch(query))

    def find_records(self, query: RecordQuery | None = None) -> list[Record]:
        return copy.deepcopy(self._state.find_records(query))

    def find_open_operations(self, lane: str, limit: int | None = None) -> list[Record]:
        return copy.deepcopy(self._state.find_open_operations(lane, limit))

    def get_log(self, after_seq: int | None = None, limit: int | None = None) -> list[LogItem]:
        return copy.deepcopy(self._state.get_log(after_seq, limit))

    def get_name(self) -> str | None:
        return self._state.get_name()

    def set_name(self, name: str | None) -> None:
        self._append_mutation(
            {"kind": "fact", "seq": self._state.next_sequence, "fact": "name", "name": name}
        )

    def get_label(self, entry_id: str) -> str | None:
        return self._state.get_label(entry_id)

    def set_label(self, entry_id: str, label: str | None) -> None:
        self._state.validate_target(entry_id)
        self._append_mutation(
            {
                "kind": "fact",
                "seq": self._state.next_sequence,
                "fact": "label",
                "target_id": entry_id,
                "label": label,
            }
        )

    def get_stats(self) -> SessionStats:
        return copy.deepcopy(self._state.get_stats())

    def close(self) -> None:
        """关闭持有的 ORM 会话，释放连接。"""
        self._db.close()


class SqliteSessionRepo:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    def create(self, options: CreateOptions | None = None) -> Session:
        options = options or CreateOptions()
        session_key = options.session_key or uuid4().hex
        db = self._session_factory()
        try:
            if db.scalar(
                select(SessionTreeSession.id).where(SessionTreeSession.session_key == session_key)
            ):
                raise SessionError("already_exists", f"Session already exists: {session_key}")
            row = SessionTreeSession(
                session_key=session_key,
                parent_session_key=options.parent_session_key,
                created_at=now_ms(),
            )
            db.add(row)
            db.flush()
            metadata = self._metadata_from_row(row)
            storage = SqliteSessionStorage(db, row.id, metadata)
            db.commit()
            return Session(storage)
        except Exception:
            db.rollback()
            db.close()
            raise

    def open(self, metadata: SessionMetadata) -> Session:
        db = self._session_factory()
        row = self._require_session_row(db, metadata.session_key)
        return Session(SqliteSessionStorage(db, row.id, self._metadata_from_row(row)))

    def list(self) -> SessionMetadataList:
        db = self._session_factory()
        try:
            rows = db.scalars(
                select(SessionTreeSession).order_by(SessionTreeSession.created_at.desc())
            ).all()
            return [self._metadata_from_row(row) for row in rows]
        finally:
            db.close()

    def find_metadata(self, session_key: str) -> SessionMetadata | None:
        db = self._session_factory()
        try:
            row = db.scalar(
                select(SessionTreeSession).where(
                    SessionTreeSession.session_key == session_key
                )
            )
            return self._metadata_from_row(row) if row is not None else None
        finally:
            db.close()

    def delete(self, metadata: SessionMetadata) -> None:
        db = self._session_factory()
        try:
            row = self._require_session_row(db, metadata.session_key)
            db.execute(
                delete(SessionTreeMutation).where(SessionTreeMutation.session_id == row.id)
            )
            db.delete(row)
            db.commit()
        finally:
            db.close()

    def fork(
        self,
        source: SessionMetadata,
        options: ForkOptions,
        create_options: CreateOptions | None = None,
    ) -> Session:
        create_options = create_options or CreateOptions()
        db = self._session_factory()
        try:
            source_row = self._require_session_row(db, source.session_key)
            source_storage = SqliteSessionStorage(
                db, source_row.id, self._metadata_from_row(source_row)
            )

            session_key = create_options.session_key or uuid4().hex
            if db.scalar(
                select(SessionTreeSession.id).where(SessionTreeSession.session_key == session_key)
            ):
                raise SessionError("already_exists", f"Session already exists: {session_key}")

            new_row = SessionTreeSession(
                session_key=session_key,
                parent_session_key=create_options.parent_session_key or source.session_key,
                created_at=now_ms(),
            )
            db.add(new_row)
            db.flush()
            new_storage = SqliteSessionStorage(db, new_row.id, self._metadata_from_row(new_row))

            mutations = source_storage._state.create_fork_mutations(options)
            for mutation in mutations:
                new_storage._persist(mutation)
            db.commit()
            for mutation in mutations:
                new_storage._state.apply_mutation(mutation)
            return Session(new_storage)
        except Exception:
            db.rollback()
            db.close()
            raise

    # ---- internal ----

    @staticmethod
    def _metadata_from_row(row: SessionTreeSession) -> SessionMetadata:
        return SessionMetadata(
            session_key=row.session_key,
            parent_session_key=row.parent_session_key,
            created_at=row.created_at,
        )

    def _require_session_row(self, db: OrmSession, session_key: str) -> SessionTreeSession:
        row = db.scalar(
            select(SessionTreeSession).where(SessionTreeSession.session_key == session_key)
        )
        if row is None:
            raise SessionError("not_found", f"Session not found: {session_key}")
        return row
