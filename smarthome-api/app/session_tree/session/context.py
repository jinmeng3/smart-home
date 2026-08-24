"""从会话树构建 LLM 上下文（压缩替换 + 扩展投影）。

树本身不是直接喂给 LLM 的内容，这里负责投影：

1. 沿路径推导最新生效的 thinkingLevel / model / activeTools。
2. 条目变换（默认：用最后一个 compaction 节点替换压缩前的历史）。
3. 条目 -> LLM 消息（compaction 摘要 + retainedTail、branch_summary、
   deferred 消息跳过、custom 投影器）。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from app.session_tree.messages import (
    create_branch_summary_message,
    create_compaction_summary_message,
)
from app.session_tree.session.types import Entry, Message

EntryTransform = Callable[[Sequence[Entry]], Sequence[Entry]]
EntryProjector = Callable[[Entry, int, Sequence[Entry]], Sequence[Message] | None]


def derive_session_context_state(path_entries: Sequence[Entry]) -> dict[str, Any]:
    thinking_level = "off"
    model: dict[str, Any] | None = None
    active_tool_names: list[str] | None = None

    for entry in path_entries:
        if entry.type == "thinking_level_change":
            thinking_level = entry.thinking_level or "off"
        elif entry.type == "model_change":
            model = {"provider": entry.provider, "modelId": entry.model_id}
        elif entry.type == "message" and entry.message and entry.message.get("role") == "assistant":
            model = {
                "provider": entry.message.get("provider"),
                "modelId": entry.message.get("model"),
            }
        elif entry.type == "active_tools_change":
            active_tool_names = list(entry.active_tool_names or [])

    return {"thinkingLevel": thinking_level, "model": model, "activeToolNames": active_tool_names}


def default_context_entry_transform(path_entries: Sequence[Entry]) -> list[Entry]:
    compaction_index = -1
    for index in range(len(path_entries) - 1, -1, -1):
        if path_entries[index].type == "compaction":
            compaction_index = index
            break
    if compaction_index == -1:
        return list(path_entries)
    return [path_entries[compaction_index], *list(path_entries[compaction_index + 1 :])]


def build_context_entries(
    path_entries: Sequence[Entry],
    entry_transforms: Sequence[EntryTransform] | None = None,
) -> list[Entry]:
    entries = default_context_entry_transform(path_entries)
    for transform in entry_transforms or []:
        entries = list(transform(entries))
    return entries


def session_entry_to_context_messages(
    entry: Entry,
    index: int,
    entries: Sequence[Entry],
    entry_projectors: dict[str, EntryProjector] | None = None,
) -> list[Message]:
    if entry.type == "message":
        message = entry.message or {}
        if message.get("role") == "assistant" and message.get("stopReason") == "deferred":
            return []
        return [message]
    if entry.type == "compaction":
        summary = create_compaction_summary_message(
            entry.summary or "",
            entry.tokens_before or 0,
            entry.timestamp,
        )
        return [summary, *(entry.retained_tail or [])]
    if entry.type == "branch_summary" and entry.summary:
        return [create_branch_summary_message(entry.summary, entry.from_id or "", entry.timestamp)]
    if entry.type == "custom":
        projector = (entry_projectors or {}).get(entry.custom_type or "")
        if projector is not None:
            projected = projector(entry, index, entries)
            return list(projected) if projected else []
        return []
    return []


def build_session_context(
    path_entries: Sequence[Entry],
    entry_transforms: Sequence[EntryTransform] | None = None,
    entry_projectors: dict[str, EntryProjector] | None = None,
) -> dict[str, Any]:
    state = derive_session_context_state(path_entries)
    context_entries = build_context_entries(path_entries, entry_transforms)
    messages: list[Message] = []
    for index, entry in enumerate(context_entries):
        messages.extend(session_entry_to_context_messages(entry, index, context_entries, entry_projectors))
    return {**state, "messages": messages}
