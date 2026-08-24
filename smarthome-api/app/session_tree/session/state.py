"""``SessionState``：纯内存状态机，所有不变式在此校验。

任何写入都经过 :meth:`SessionState.apply_mutation` 统一校验，保证：

1. ``seq`` 连续（每次 +1）。
2. entry / record 的 ``id`` 全局唯一。
3. lane 必须存在。
4. entry 的 ``parent_id`` 必须链到当前车道的 leaf。
5. ``parent_id`` 非空时父节点必须存在。
6. record 的 lane 必须存在；label fact 的 target 必须存在。

查询系统（find_entries / find_entries_on_branch / find_records / walk_to_root）
与分支分叉（create_fork_mutations）也在此实现。
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterator
from typing import Any

from app.session_tree.errors import SessionError
from app.session_tree.session.types import (
    Entry,
    EntryQuery,
    ForkOptions,
    LanePointer,
    LogItem,
    Record,
    RecordQuery,
    SessionStats,
)


def _assert_valid_limit(limit: int | None) -> None:
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise SessionError("invalid_query", "limit must be a positive integer")


def _assert_valid_cursor(after_seq: int | None) -> None:
    if after_seq is not None and (not isinstance(after_seq, int) or after_seq < 0):
        raise SessionError(
            "invalid_query", "cursor sequence must be a non-negative integer"
        )


def _ordered(items: list[Any], order: str) -> Iterator[Any]:
    if order == "oldestFirst":
        yield from items
        return
    for index in range(len(items) - 1, -1, -1):
        yield items[index]


class SessionState:
    def __init__(self) -> None:
        self._sequence = 0
        self._used_ids: set[str] = set()
        self._entries: list[Entry] = []
        self._entries_by_id: dict[str, Entry] = {}
        self._records: list[Record] = []
        self._open_operations_by_lane: dict[str, dict[str, Record]] = {}
        self._lanes: dict[str, str | None] = {"main": None}
        self._log: list[LogItem] = []
        self._stats = SessionStats()
        self._name: str | None = None
        self._labels: dict[str, str] = {}

    @property
    def next_sequence(self) -> int:
        return self._sequence + 1

    # ---- lanes ----

    def get_lanes(self) -> list[LanePointer]:
        return [LanePointer(lane, leaf_id) for lane, leaf_id in self._lanes.items()]

    def require_lane(self, lane: str) -> str | None:
        if lane not in self._lanes:
            raise SessionError("invalid_lane", f"Lane not found: {lane}")
        return self._lanes[lane]

    def validate_new_lane(self, lane: str) -> None:
        if lane in self._lanes:
            raise SessionError("already_exists", f"Lane already exists: {lane}")

    def validate_target(self, target_id: str | None) -> None:
        if target_id is not None and target_id not in self._entries_by_id:
            raise SessionError("not_found", f"Entry not found: {target_id}")

    def validate_unused_id(self, entry_id: str) -> None:
        if entry_id in self._used_ids:
            raise SessionError(
                "already_exists", f"Session id already exists: {entry_id}"
            )

    # ---- mutation application ----

    def apply_mutation(
        self,
        mutation: dict[str, Any],
        invalid: Callable[[str], Any] | None = None,
    ) -> None:
        def fail(message: str) -> None:
            if invalid is not None:
                invalid(message)
            raise SessionError("invalid_entry", f"Invalid session mutation: {message}")

        kind = mutation["kind"]
        if kind == "entry":
            seq = mutation["entry"].seq
        elif kind == "record":
            seq = mutation["record"].seq
        else:
            seq = mutation["seq"]

        if seq != self._sequence + 1:
            fail(f"has non-consecutive seq {seq}")

        if kind == "entry":
            entry: Entry = mutation["entry"]
            if entry.id in self._used_ids:
                fail(f"contains duplicate id {entry.id}")
            lane = mutation.get("lane")
            if lane is not None:
                leaf_id = self._lanes.get(lane)
                if leaf_id is None and lane not in self._lanes:
                    fail(f"references missing lane {lane}")
                if entry.parent_id != self._lanes[lane]:
                    fail("does not chain to the lane leaf")
            if (
                entry.parent_id is not None
                and entry.parent_id not in self._entries_by_id
            ):
                fail(f"references missing parent {entry.parent_id}")

            self._sequence = seq
            self._used_ids.add(entry.id)
            self._entries.append(entry)
            self._entries_by_id[entry.id] = entry
            if lane is not None:
                self._lanes[lane] = entry.id
            self._log.append(LogItem(kind="entry", seq=seq, entry=entry))
            if entry.type == "message":
                self._stats.message_count += 1
            return

        if kind == "record":
            record: Record = mutation["record"]
            if record.lane not in self._lanes:
                fail(f"references missing lane {record.lane}")
            if record.id in self._used_ids:
                fail(f"contains duplicate id {record.id}")

            self._sequence = seq
            self._used_ids.add(record.id)
            self._records.append(record)
            if record.type == "operation_started":
                self._open_operations_by_lane.setdefault(record.lane, {})[record.id] = (
                    record
                )
            elif record.type == "operation_finished" and record.run_id is not None:
                self._open_operations_by_lane.get(record.lane, {}).pop(
                    record.run_id, None
                )
            self._log.append(LogItem(kind="record", seq=seq, record=record))
            if record.type == "usage" and isinstance(record.usage, dict):
                self._stats.cached_tokens += int(record.usage.get("cacheRead", 0) or 0)
                self._stats.uncached_tokens += int(
                    record.usage.get("input", 0) or 0
                ) + int(record.usage.get("cacheWrite", 0) or 0)
                self._stats.total_tokens += int(record.usage.get("totalTokens", 0) or 0)
                cost = record.usage.get("cost") or {}
                self._stats.cost_total += float(cost.get("total", 0) or 0)
            return

        if kind == "lane":
            leaf_id = mutation["leaf_id"]
            if leaf_id is not None and leaf_id not in self._entries_by_id:
                fail(f"references missing lane target {leaf_id}")
            self._sequence = seq
            self._lanes[mutation["lane"]] = leaf_id
            self._log.append(
                LogItem(kind="lane", seq=seq, lane=mutation["lane"], leaf_id=leaf_id)
            )
            return

        if kind == "fact":
            if (
                mutation["fact"] == "label"
                and mutation["target_id"] not in self._entries_by_id
            ):
                fail(f"references missing label target {mutation['target_id']}")
            self._sequence = seq
            if mutation["fact"] == "name":
                self._name = mutation["name"]
                self._log.append(
                    LogItem(kind="fact", seq=seq, fact="name", name=mutation["name"])
                )
            else:
                target_id = mutation["target_id"]
                label = mutation["label"]
                if label is None:
                    self._labels.pop(target_id, None)
                else:
                    self._labels[target_id] = label
                self._log.append(
                    LogItem(
                        kind="fact",
                        seq=seq,
                        fact="label",
                        target_id=target_id,
                        label=label,
                    )
                )
            return

        fail(f"unknown mutation kind {kind}")

    # ---- reads ----

    def get_entry(self, entry_id: str) -> Entry | None:
        return self._entries_by_id.get(entry_id)

    def find_entries(self, query: EntryQuery | None = None) -> list[Entry]:
        query = query or EntryQuery()
        _assert_valid_limit(query.limit)
        _assert_valid_cursor(query.after_seq)

        results: list[Entry] = []
        for entry in _ordered(self._entries, query.order):
            if not self._matches_entry_query(entry, query):
                continue
            results.append(entry)
            if len(results) == query.limit:
                break
        return results

    def find_entries_on_branch(self, query: EntryQuery) -> list[Entry]:
        _assert_valid_limit(query.limit)
        _assert_valid_cursor(query.after_seq)

        results: list[Entry] = []
        if query.order == "oldestFirst":
            # 与源码一致：oldestFirst 先遍历完整路径到根（不带边界），反转后
            # 在循环里按 stopAtId / stopAtType 作为边界中断。
            path = list(self._walk_to_root(query.start))[::-1]
            for entry in path:
                reached_bound = (
                    entry.id == query.stop_at_id or entry.type == query.stop_at_type
                )
                if self._matches_entry_query(entry, query):
                    results.append(entry)
                if reached_bound or len(results) == query.limit:
                    break
        else:
            for entry in self._walk_to_root(
                query.start, query.stop_at_id, query.stop_at_type
            ):
                if self._matches_entry_query(entry, query):
                    results.append(entry)
                if len(results) == query.limit:
                    break
        return results

    def find_records(self, query: RecordQuery | None = None) -> list[Record]:
        query = query or RecordQuery()
        _assert_valid_limit(query.limit)
        _assert_valid_cursor(query.after_seq)

        results: list[Record] = []
        for record in _ordered(self._records, query.order):
            if not self._matches_record_query(record, query):
                continue
            results.append(record)
            if len(results) == query.limit:
                break
        return results

    def find_open_operations(self, lane: str, limit: int | None = None) -> list[Record]:
        _assert_valid_limit(limit)
        open_operations = list(self._open_operations_by_lane.get(lane, {}).values())
        open_operations.reverse()
        return open_operations if limit is None else open_operations[:limit]

    def get_log(
        self, after_seq: int | None = None, limit: int | None = None
    ) -> list[LogItem]:
        _assert_valid_limit(limit)
        _assert_valid_cursor(after_seq)

        results: list[LogItem] = []
        for item in self._log:
            if after_seq is not None and item.seq <= after_seq:
                continue
            results.append(item)
            if len(results) == limit:
                break
        return results

    def get_name(self) -> str | None:
        return self._name

    def get_label(self, entry_id: str) -> str | None:
        return self._labels.get(entry_id)

    def get_stats(self) -> SessionStats:
        return copy.deepcopy(self._stats)

    # ---- fork ----

    def create_fork_mutations(self, options: ForkOptions) -> list[dict[str, Any]]:
        if options.scope == "tree":
            copied_entries = self.find_entries(EntryQuery(order="oldestFirst"))
            fork_lanes = self.get_lanes()
        else:
            selected_entry_id = (
                options.entry_id
                if options.entry_id is not None
                else self.require_lane("main")
            )
            target_id: str | None = None
            if selected_entry_id is not None:
                entry = self.get_entry(selected_entry_id)
                if entry is None or entry.type != "message":
                    raise SessionError(
                        "invalid_fork_target",
                        f"Fork target is not a message entry: {selected_entry_id}",
                    )
                position = options.position or (
                    "at" if options.entry_id is None else "before"
                )
                target_id = entry.id if position == "at" else entry.parent_id
            if target_id is None:
                copied_entries = []
            else:
                copied_entries = self.find_entries_on_branch(
                    EntryQuery(order="oldestFirst", start=target_id),
                )
            fork_lanes = [LanePointer("main", target_id)]

        mutations: list[dict[str, Any]] = []
        sequence = 1
        for source_entry in copied_entries:
            entry = copy.deepcopy(source_entry)
            entry.seq = sequence
            sequence += 1
            mutations.append({"kind": "entry", "entry": entry})
        for pointer in fork_lanes:
            mutations.append(
                {
                    "kind": "lane",
                    "seq": sequence,
                    "lane": pointer.lane,
                    "leaf_id": pointer.leaf_id,
                }
            )
            sequence += 1
        if self._name is not None:
            mutations.append(
                {"kind": "fact", "seq": sequence, "fact": "name", "name": self._name}
            )
            sequence += 1
        for entry in copied_entries:
            label = self._labels.get(entry.id)
            if label is not None:
                mutations.append(
                    {
                        "kind": "fact",
                        "seq": sequence,
                        "fact": "label",
                        "target_id": entry.id,
                        "label": label,
                    }
                )
                sequence += 1
        return mutations

    # ---- internal ----

    def _walk_to_root(
        self,
        start: str | None,
        stop_at_id: str | None = None,
        stop_at_type: str | None = None,
    ) -> Iterator[Entry]:
        if start is None:
            return
        visited: set[str] = set()
        current = self._entries_by_id.get(start)
        if current is None:
            raise SessionError("not_found", f"Entry not found: {start}")
        while current is not None:
            if current.id in visited:
                raise SessionError(
                    "invalid_entry", f"Session branch contains a cycle at {current.id}"
                )
            visited.add(current.id)
            yield current
            if (
                current.id == stop_at_id
                or current.type == stop_at_type
                or current.parent_id is None
            ):
                break
            parent_id = current.parent_id
            current = self._entries_by_id.get(parent_id)  # type: ignore[assignment]
            if current is None:
                raise SessionError("invalid_entry", f"Entry not found: {parent_id}")

    def _matches_entry_query(self, entry: Entry, query: EntryQuery) -> bool:
        type_match = query.type is None or entry.type == query.type
        custom_match = query.custom_type is None or (
            entry.type == "custom" and entry.custom_type == query.custom_type
        )
        if query.after_seq is None:
            cursor_match = True
        elif query.order == "oldestFirst":
            cursor_match = entry.seq > query.after_seq
        else:
            cursor_match = entry.seq < query.after_seq
        return type_match and custom_match and cursor_match

    def _matches_record_query(self, record: Record, query: RecordQuery) -> bool:
        if query.lane is not None and record.lane != query.lane:
            return False
        if query.type is not None and record.type != query.type:
            return False
        if query.run_id is not None:
            if record.type == "operation_started":
                if record.id != query.run_id:
                    return False
            elif record.run_id != query.run_id:
                return False
        if query.operation_kind is not None:
            if record.type != "operation_started":
                return False
            intent = record.intent if isinstance(record.intent, dict) else {}
            if intent.get("kind") != query.operation_kind:
                return False
        return query.after_seq is None or record.seq > query.after_seq
