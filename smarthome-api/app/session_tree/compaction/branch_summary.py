"""分支摘要的树导航与条目准备（纯逻辑，不含 LLM 调用）。

对应文档 §8.2：计算旧 leaf 与目标节点的公共祖先，收集被抛弃分支上的条目。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.session_tree.compaction.compaction import (
    FileOperations,
    create_file_ops,
    estimate_tokens,
    extract_file_ops_from_message,
)
from app.session_tree.errors import SessionError
from app.session_tree.messages import (
    create_branch_summary_message,
    create_compaction_summary_message,
)
from app.session_tree.session.types import Entry, EntryQuery, Message

if TYPE_CHECKING:  # pragma: no cover - 仅用于类型标注
    from app.session_tree.session.storage import Session


@dataclass
class CollectEntriesResult:
    entries: list[Entry]
    common_ancestor_id: str | None


@dataclass
class BranchPreparation:
    messages: list[Message]
    file_ops: FileOperations
    total_tokens: int


def collect_entries_for_branch_summary(
    session: Session,
    old_leaf_id: str | None,
    target_id: str,
) -> CollectEntriesResult:
    if not old_leaf_id:
        return CollectEntriesResult([], None)

    old_path = {
        entry.id for entry in session.find_entries_on_branch(EntryQuery(start=old_leaf_id))
    }
    target_path = session.find_entries_on_branch(EntryQuery(start=target_id))

    common_ancestor_id: str | None = None
    for entry in target_path:
        if entry.id in old_path:
            common_ancestor_id = entry.id
            break

    entries: list[Entry] = []
    current: str | None = old_leaf_id
    while current and current != common_ancestor_id:
        entry = session.get_entry(current)
        if entry is None:
            raise SessionError("invalid_entry", f"Entry {current} not found")
        entries.append(entry)
        current = entry.parent_id
    entries.reverse()

    return CollectEntriesResult(entries=entries, common_ancestor_id=common_ancestor_id)


def _get_message_from_entry(entry: Entry) -> Message | None:
    if entry.type == "message":
        message = entry.message or {}
        if message.get("role") == "toolResult":
            return None
        return message
    if entry.type == "branch_summary":
        return create_branch_summary_message(
            entry.summary or "", entry.from_id or "", entry.timestamp
        )
    if entry.type == "compaction":
        return create_compaction_summary_message(
            entry.summary or "", entry.tokens_before or 0, entry.timestamp
        )
    return None


def prepare_branch_entries(entries: list[Entry], token_budget: int = 0) -> BranchPreparation:
    messages: list[Message] = []
    file_ops = create_file_ops()
    total_tokens = 0

    for entry in entries:
        if entry.type == "branch_summary" and isinstance(entry.details, dict):
            details = entry.details
            read_files = details.get("readFiles")
            modified_files = details.get("modifiedFiles")
            if isinstance(read_files, list):
                for path in read_files:
                    if isinstance(path, str):
                        file_ops.read.add(path)
            if isinstance(modified_files, list):
                for path in modified_files:
                    if isinstance(path, str):
                        file_ops.edited.add(path)

    for i in range(len(entries) - 1, -1, -1):
        entry = entries[i]
        message = _get_message_from_entry(entry)
        if message is None:
            continue

        extract_file_ops_from_message(message, file_ops)
        tokens = estimate_tokens(message)
        if token_budget > 0 and total_tokens + tokens > token_budget:
            if entry.type in ("compaction", "branch_summary") and total_tokens < token_budget * 0.9:
                messages.insert(0, message)
                total_tokens += tokens
            break
        messages.insert(0, message)
        total_tokens += tokens

    return BranchPreparation(messages=messages, file_ops=file_ops, total_tokens=total_tokens)
