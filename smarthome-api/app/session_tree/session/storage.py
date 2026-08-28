"""存储抽象与门面。

- ``SessionStorage``：存储实现协议（内存版与 SQLite 版共享同一接口）。
- ``Session``：面向使用方的读写门面，提供 ``view(lane)``、``append_message``
  等高层 API。
- ``InMemorySessionStorage``：内存实现，用于测试与快速原型。
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any, Protocol
from uuid import uuid4

from app.session_tree.errors import SessionError
from app.utils.time import now_utc_ms
from app.session_tree.session.state import SessionState
from app.session_tree.session.types import (
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


def now_ms() -> int:
    return now_utc_ms()


class SessionStorage(Protocol):
    def get_metadata(self) -> SessionMetadata: ...
    def get_lanes(self) -> list[LanePointer]: ...
    def create_lane(self, lane: str, at: str | None) -> None: ...
    def move_lane(self, lane: str, to: str | None) -> None: ...
    def append_entry(self, entry: Entry, lane: str) -> Entry: ...
    def append_record(self, record: Record) -> Record: ...
    def get_entry(self, entry_id: str) -> Entry | None: ...
    def find_entries(self, query: EntryQuery | None = None) -> list[Entry]: ...
    def find_entries_on_branch(self, query: EntryQuery) -> list[Entry]: ...
    def find_records(self, query: RecordQuery | None = None) -> list[Record]: ...
    def find_open_operations(self, lane: str, limit: int | None = None) -> list[Record]: ...
    def get_log(self, after_seq: int | None = None, limit: int | None = None) -> list[LogItem]: ...
    def get_name(self) -> str | None: ...
    def set_name(self, name: str | None) -> None: ...
    def get_label(self, entry_id: str) -> str | None: ...
    def set_label(self, entry_id: str, label: str | None) -> None: ...
    def get_stats(self) -> SessionStats: ...
    def close(self) -> None: ...


class _LaneView:
    """非 main 车道的只针对该车道的树视图。"""

    def __init__(self, session: Session, lane: str) -> None:
        self._session = session
        self._lane = lane

    def get_leaf_id(self) -> str | None:
        return self._session._get_leaf_id_for_lane(self._lane)

    def get_entry(self, entry_id: str) -> Entry | None:
        return self._session.get_entry(entry_id)

    def get_stats(self) -> SessionStats:
        return self._session.get_stats()

    def get_name(self) -> str | None:
        return self._session.get_name()

    def set_name(self, name: str | None) -> None:
        self._session.set_name(name)

    def get_label(self, target_id: str) -> str | None:
        return self._session.get_label(target_id)

    def set_label(self, target_id: str, label: str | None) -> None:
        self._session.set_label(target_id, label)

    def find_entries(self, query: EntryQuery | None = None) -> list[Entry]:
        return self._session.find_entries(query)

    def find_entry(self, query: EntryQuery | None = None) -> Entry | None:
        return self._session.find_entry(query)

    def find_entries_on_branch(self, query: EntryQuery | None = None) -> list[Entry]:
        return self._session._query_branch_entries(self._lane, query)

    def find_entry_on_branch(self, query: EntryQuery | None = None) -> Entry | None:
        results = self._session._query_branch_entries(self._lane, query, 1)
        return results[0] if results else None

    def append_message(self, message: dict[str, Any]) -> str:
        return self._session._append_message_to_lane(self._lane, message)

    def append_custom_entry(self, custom_type: str, data: Any = None) -> str:
        return self._session._append_custom_entry_to_lane(self._lane, custom_type, data)


class Session:
    """会话读写门面（``main`` 视图即 Session 本身）。"""

    def __init__(
        self,
        storage: SessionStorage,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._storage = storage
        self._id_factory = id_factory or (lambda: uuid4().hex)

    # ---- metadata / facts ----

    def get_metadata(self) -> SessionMetadata:
        return self._storage.get_metadata()

    def get_name(self) -> str | None:
        return self._storage.get_name()

    def set_name(self, name: str | None) -> None:
        self._storage.set_name(name)

    def get_label(self, target_id: str) -> str | None:
        return self._storage.get_label(target_id)

    def set_label(self, target_id: str, label: str | None) -> None:
        self._storage.set_label(target_id, label)

    def get_stats(self) -> SessionStats:
        return self._storage.get_stats()

    def close(self) -> None:
        """释放底层存储资源（SQLite 实现会关闭其持有的 ORM 会话）。"""
        self._storage.close()

    def get_entry(self, entry_id: str) -> Entry | None:
        return self._storage.get_entry(entry_id)

    # ---- lanes ----

    def view(self, lane: str) -> _LaneView | Session:
        if lane == "main":
            return self
        return _LaneView(self, lane)

    def get_leaf_id(self) -> str | None:
        return self._get_leaf_id_for_lane("main")

    def get_lanes(self) -> list[LanePointer]:
        return self._storage.get_lanes()

    def create_lane(self, lane: str, at: str | None) -> None:
        self._storage.create_lane(lane, at)

    def move_lane(self, lane: str, to: str | None) -> None:
        self._storage.move_lane(lane, to)

    # ---- entries / records ----

    def append_entry(self, entry: Entry, lane: str) -> Entry:
        return self._storage.append_entry(entry, lane)

    def append_record(self, record: Record) -> Record:
        return self._storage.append_record(record)

    def append_message(self, message: dict[str, Any]) -> str:
        return self._append_message_to_lane("main", message)

    def append_custom_entry(self, custom_type: str, data: Any = None) -> str:
        return self._append_custom_entry_to_lane("main", custom_type, data)

    # ---- queries ----

    def find_entries(self, query: EntryQuery | None = None) -> list[Entry]:
        return self._storage.find_entries(query)

    def find_entry(self, query: EntryQuery | None = None) -> Entry | None:
        results = self._storage.find_entries(_with_limit(query, 1))
        return results[0] if results else None

    def find_entries_on_branch(self, query: EntryQuery | None = None) -> list[Entry]:
        return self._query_branch_entries("main", query)

    def find_entry_on_branch(self, query: EntryQuery | None = None) -> Entry | None:
        results = self._query_branch_entries("main", query, 1)
        return results[0] if results else None

    def find_records(self, query: RecordQuery | None = None) -> list[Record]:
        query = query or RecordQuery()
        if query.operation_kind is not None and query.type != "operation_started":
            raise SessionError("invalid_query", 'operationKind requires type "operation_started"')
        return self._storage.find_records(query)

    def find_open_operations(self, lane: str, limit: int | None = None) -> list[Record]:
        return self._storage.find_open_operations(lane, limit)

    def get_log(self, after_seq: int | None = None, limit: int | None = None) -> list[LogItem]:
        return self._storage.get_log(after_seq, limit)

    # ---- internal ----

    def _get_leaf_id_for_lane(self, lane: str) -> str | None:
        pointer = next((p for p in self.get_lanes() if p.lane == lane), None)
        if pointer is None:
            raise SessionError("invalid_lane", f"Lane not found: {lane}")
        return pointer.leaf_id

    def _query_branch_entries(
        self,
        default_lane: str,
        query: EntryQuery | None = None,
        result_limit: int | None = None,
    ) -> list[Entry]:
        query = copy.deepcopy(query) if query else EntryQuery()
        if query.start is None:
            query.start = self._get_leaf_id_for_lane(default_lane)
        if query.start is None:
            return []
        if result_limit is not None:
            query.limit = result_limit
        return self._storage.find_entries_on_branch(query)

    def _append_message_to_lane(self, lane: str, message: dict[str, Any]) -> str:
        entry = Entry(type="message", id=self._id_factory(), message=message)
        return self._storage.append_entry(entry, lane).id

    def _append_custom_entry_to_lane(self, lane: str, custom_type: str, data: Any = None) -> str:
        entry = Entry(type="custom", id=self._id_factory(), custom_type=custom_type, data=data)
        return self._storage.append_entry(entry, lane).id


def _with_limit(query: EntryQuery | None, limit: int) -> EntryQuery:
    query = copy.deepcopy(query) if query else EntryQuery()
    query.limit = limit
    return query


class InMemorySessionStorage:
    def __init__(self, metadata: SessionMetadata) -> None:
        self._metadata = copy.deepcopy(metadata)
        self._state = SessionState()

    def fork(self, metadata: SessionMetadata, options: ForkOptions) -> InMemorySessionStorage:
        storage = InMemorySessionStorage(metadata)
        for mutation in self._state.create_fork_mutations(options):
            storage._state.apply_mutation(mutation)
        return storage

    def get_metadata(self) -> SessionMetadata:
        return copy.deepcopy(self._metadata)

    def get_lanes(self) -> list[LanePointer]:
        return self._state.get_lanes()

    def create_lane(self, lane: str, at: str | None) -> None:
        self._state.validate_new_lane(lane)
        self._state.validate_target(at)
        self._state.apply_mutation(
            {"kind": "lane", "seq": self._state.next_sequence, "lane": lane, "leaf_id": at}
        )

    def move_lane(self, lane: str, to: str | None) -> None:
        self._state.require_lane(lane)
        self._state.validate_target(to)
        self._state.apply_mutation(
            {"kind": "lane", "seq": self._state.next_sequence, "lane": lane, "leaf_id": to}
        )

    def append_entry(self, entry: Entry, lane: str) -> Entry:
        parent_id = self._state.require_lane(lane)
        self._state.validate_unused_id(entry.id)
        entry.parent_id = parent_id
        entry.seq = self._state.next_sequence
        entry.timestamp = now_ms()
        self._state.apply_mutation({"kind": "entry", "lane": lane, "entry": entry})
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
        self._state.apply_mutation({"kind": "record", "record": record})
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
        self._state.apply_mutation(
            {"kind": "fact", "seq": self._state.next_sequence, "fact": "name", "name": name}
        )

    def get_label(self, entry_id: str) -> str | None:
        return self._state.get_label(entry_id)

    def set_label(self, entry_id: str, label: str | None) -> None:
        self._state.validate_target(entry_id)
        self._state.apply_mutation(
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
        """内存实现无底层资源，关闭为无操作。"""
