"""对象 <-> JSON 字典的编解码。

SQLite 持久化层把每条 mutation 序列化为 JSON 保存。这里的编解码只负责
把 ``Entry`` / ``Record`` 等 dataclass 与 JSON 兼容字典互转，并在读取时
对关键字段做轻量校验（未知类型、坏结构会抛 :class:`SessionError`）。
"""

from __future__ import annotations

from dataclasses import asdict, fields
from typing import Any

from app.session_tree.errors import SessionError
from app.session_tree.session.types import Entry, Record

ENTRY_TYPES = {
    "message",
    "model_change",
    "thinking_level_change",
    "active_tools_change",
    "compaction",
    "branch_summary",
    "custom",
}

RECORD_TYPES = {
    "operation_started",
    "abort_requested",
    "operation_finished",
    "step_attempt",
    "tool_started",
    "queue_enqueued",
    "queue_cancelled",
    "write_deferred",
    "usage",
}

_ENTRY_FIELDS = {f.name for f in fields(Entry)}
_RECORD_FIELDS = {f.name for f in fields(Record)}


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    """去掉值为 ``None`` 的字段，使 JSON 载荷与 TypeScript 判别联合体一致。"""
    return {key: value for key, value in data.items() if value is not None}


def entry_to_dict(entry: Entry) -> dict[str, Any]:
    return _compact(asdict(entry))


def record_to_dict(record: Record) -> dict[str, Any]:
    return _compact(asdict(record))


def entry_from_dict(data: dict[str, Any]) -> Entry:
    entry_type = data.get("type")
    if entry_type not in ENTRY_TYPES:
        raise SessionError("invalid_entry", f"unknown entry type: {entry_type}")
    return Entry(**{key: value for key, value in data.items() if key in _ENTRY_FIELDS})


def record_from_dict(data: dict[str, Any]) -> Record:
    record_type = data.get("type")
    if record_type not in RECORD_TYPES:
        raise SessionError("invalid_entry", f"unknown record type: {record_type}")
    if not isinstance(data.get("lane"), str):
        raise SessionError("invalid_entry", "record is missing a lane")
    return Record(**{key: value for key, value in data.items() if key in _RECORD_FIELDS})


def mutation_to_dict(mutation: dict[str, Any]) -> dict[str, Any]:
    """把内存中的 mutation（entry/record 为 dataclass）序列化为 JSON 字典。"""
    if mutation["kind"] == "entry":
        return {
            "kind": "entry",
            "lane": mutation.get("lane"),
            "entry": entry_to_dict(mutation["entry"]),
        }
    if mutation["kind"] == "record":
        return {"kind": "record", "record": record_to_dict(mutation["record"])}
    # lane / fact mutation 本身就是 JSON 兼容字典
    return dict(mutation)


def mutation_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """把 JSON 字典反序列化为内存 mutation（entry/record 还原为 dataclass）。"""
    if data.get("kind") == "entry":
        return {
            "kind": "entry",
            "lane": data.get("lane"),
            "entry": entry_from_dict(data["entry"]),
        }
    if data.get("kind") == "record":
        return {"kind": "record", "record": record_from_dict(data["record"])}
    return dict(data)
