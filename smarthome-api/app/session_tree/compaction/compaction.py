"""上下文压缩的纯逻辑（不含 LLM 调用）。

对应文档 §8.1：从最新向前找切割点，产出待摘要历史、split turn 前缀与
保留尾巴。上次压缩的摘要参与迭代更新，上次压缩保留的消息被映射为虚拟
条目纳入下一次切割点计算。实际的摘要生成（LLM 调用）作为上层集成点。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from app.session_tree.messages import (
    create_branch_summary_message,
    create_compaction_summary_message,
)
from app.session_tree.session.context import build_session_context
from app.session_tree.session.types import CompactionSettings, Entry, Message

ESTIMATED_IMAGE_CHARS = 4800


@dataclass
class FileOperations:
    read: set[str] = field(default_factory=set)
    written: set[str] = field(default_factory=set)
    edited: set[str] = field(default_factory=set)


@dataclass
class CutPointResult:
    first_kept_entry_index: int
    turn_start_index: int
    is_split_turn: bool


@dataclass
class CompactionPreparation:
    messages_to_summarize: list[Message]
    turn_prefix_messages: list[Message]
    retained_tail: list[Message]
    is_split_turn: bool
    tokens_before: int
    previous_summary: str | None
    file_ops: FileOperations
    settings: CompactionSettings


# === 文件操作提取 ===


def create_file_ops() -> FileOperations:
    return FileOperations()


def extract_file_ops_from_message(message: Message, file_ops: FileOperations) -> None:
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "toolCall":
            continue
        args = block.get("arguments")
        name = block.get("name")
        if not isinstance(args, dict) or not isinstance(name, str):
            continue
        path = args.get("path")
        if not isinstance(path, str) or not path:
            continue
        if name == "read":
            file_ops.read.add(path)
        elif name == "write":
            file_ops.written.add(path)
        elif name == "edit":
            file_ops.edited.add(path)


def compute_file_lists(file_ops: FileOperations) -> dict[str, list[str]]:
    """把三集合文件操作转为 ``(readFiles, modifiedFiles)``（与 ``details`` 键名一致）。"""
    modified = set(file_ops.edited) | set(file_ops.written)
    read_only = sorted(f for f in file_ops.read if f not in modified)
    return {"readFiles": read_only, "modifiedFiles": sorted(modified)}


def format_file_operations(read_files: list[str], modified_files: list[str]) -> str:
    sections: list[str] = []
    if read_files:
        sections.append("<read-files>\n" + "\n".join(read_files) + "\n</read-files>")
    if modified_files:
        sections.append("<modified-files>\n" + "\n".join(modified_files) + "\n</modified-files>")
    if not sections:
        return ""
    return "\n\n" + "\n\n".join(sections)


# === token 估算 ===


def calculate_context_tokens(usage: dict[str, Any]) -> int:
    if usage.get("totalTokens"):
        return int(usage["totalTokens"])
    return (
        int(usage.get("input", 0) or 0)
        + int(usage.get("output", 0) or 0)
        + int(usage.get("cacheRead", 0) or 0)
        + int(usage.get("cacheWrite", 0) or 0)
    )


def _safe_json_stringify(value: Any) -> str:
    if value is None:
        return "undefined"
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return "[unserializable]"


def _estimate_text_image_chars(content: Any) -> int:
    if isinstance(content, str):
        return len(content)
    if not isinstance(content, list):
        return 0
    chars = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            chars += len(block["text"])
        elif block.get("type") == "image":
            chars += ESTIMATED_IMAGE_CHARS
    return chars


def estimate_tokens(message: Message) -> int:
    role = message.get("role")
    if role == "user":
        return math.ceil(_estimate_text_image_chars(message.get("content")) / 4)
    if role == "assistant":
        chars = 0
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                chars += len(block.get("text") or "")
            elif block.get("type") == "thinking":
                chars += len(block.get("thinking") or "")
            elif block.get("type") == "toolCall":
                chars += len(block.get("name") or "") + len(
                    _safe_json_stringify(block.get("arguments"))
                )
        return math.ceil(chars / 4)
    if role in ("custom", "toolResult"):
        return math.ceil(_estimate_text_image_chars(message.get("content")) / 4)
    if role == "bashExecution":
        chars = len(message.get("command") or "") + len(message.get("output") or "")
        return math.ceil(chars / 4)
    if role in ("branchSummary", "compactionSummary"):
        return math.ceil(len(message.get("summary") or "") / 4)
    return 0


def _get_assistant_usage(message: Message) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get("role") != "assistant" or "usage" not in message:
        return None
    stop_reason = message.get("stopReason")
    usage = message.get("usage")
    if stop_reason in ("aborted", "error"):
        return None
    if not isinstance(usage, dict) or calculate_context_tokens(usage) <= 0:
        return None
    return usage


def get_last_assistant_usage(entries: list[Entry]) -> dict[str, Any] | None:
    for i in range(len(entries) - 1, -1, -1):
        if entries[i].type == "message":
            usage = _get_assistant_usage(entries[i].message or {})
            if usage is not None:
                return usage
    return None


def estimate_context_tokens(messages: list[Message]) -> dict[str, Any]:
    usage_info: dict[str, Any] | None = None
    for i in range(len(messages) - 1, -1, -1):
        usage = _get_assistant_usage(messages[i])
        if usage is not None:
            usage_info = {"usage": usage, "index": i}
            break

    if usage_info is None:
        estimated = sum(estimate_tokens(message) for message in messages)
        return {
            "tokens": estimated,
            "usage_tokens": 0,
            "trailing_tokens": estimated,
            "last_usage_index": None,
        }

    usage_tokens = calculate_context_tokens(usage_info["usage"])
    trailing_tokens = sum(
        estimate_tokens(messages[i]) for i in range(usage_info["index"] + 1, len(messages))
    )
    return {
        "tokens": usage_tokens + trailing_tokens,
        "usage_tokens": usage_tokens,
        "trailing_tokens": trailing_tokens,
        "last_usage_index": usage_info["index"],
    }


def should_compact(
    context_tokens: int,
    context_window: int,
    settings: CompactionSettings,
) -> bool:
    if not settings.enabled:
        return False
    return context_tokens > context_window - settings.reserve_tokens


# === 切割点 ===


def _find_valid_cut_points(entries: list[Entry], start_index: int, end_index: int) -> list[int]:
    cut_points: list[int] = []
    for i in range(start_index, end_index):
        entry = entries[i]
        if entry.type == "message":
            role = (entry.message or {}).get("role")
            if role in (
                "bashExecution",
                "custom",
                "branchSummary",
                "compactionSummary",
                "user",
                "assistant",
            ):
                cut_points.append(i)
        if entry.type == "branch_summary":
            cut_points.append(i)
    return cut_points


def find_turn_start_index(entries: list[Entry], entry_index: int, start_index: int) -> int:
    for i in range(entry_index, start_index - 1, -1):
        entry = entries[i]
        if entry.type == "branch_summary":
            return i
        if entry.type == "message":
            role = (entry.message or {}).get("role")
            if role in ("user", "bashExecution"):
                return i
    return -1


def find_cut_point(
    entries: list[Entry],
    start_index: int,
    end_index: int,
    keep_recent_tokens: int,
) -> CutPointResult:
    cut_points = _find_valid_cut_points(entries, start_index, end_index)
    if not cut_points:
        return CutPointResult(start_index, -1, False)

    accumulated_tokens = 0
    cut_index = cut_points[0]
    for i in range(end_index - 1, start_index - 1, -1):
        entry = entries[i]
        if entry.type != "message":
            continue
        accumulated_tokens += estimate_tokens(entry.message or {})
        if accumulated_tokens >= keep_recent_tokens:
            for candidate in cut_points:
                if candidate >= i:
                    cut_index = candidate
                    break
            break

    while cut_index > start_index:
        previous = entries[cut_index - 1]
        if previous.type in ("compaction", "message"):
            break
        cut_index -= 1

    cut_entry = entries[cut_index]
    is_user_message = cut_entry.type == "message" and (cut_entry.message or {}).get("role") == "user"
    turn_start_index = -1 if is_user_message else find_turn_start_index(entries, cut_index, start_index)
    return CutPointResult(
        first_kept_entry_index=cut_index,
        turn_start_index=turn_start_index,
        is_split_turn=(not is_user_message) and turn_start_index != -1,
    )


# === 消息投影与压缩准备 ===


def get_message_from_entry(entry: Entry) -> Message | None:
    if entry.type == "message":
        return entry.message
    if entry.type == "branch_summary":
        return create_branch_summary_message(
            entry.summary or "", entry.from_id or "", entry.timestamp
        )
    if entry.type == "compaction":
        return create_compaction_summary_message(
            entry.summary or "", entry.tokens_before or 0, entry.timestamp
        )
    return None


def _get_message_from_entry_for_compaction(entry: Entry) -> Message | None:
    if entry.type == "compaction":
        return None
    return get_message_from_entry(entry)


def _extract_file_operations(
    messages: list[Message],
    entries: list[Entry],
    prev_compaction_index: int,
) -> FileOperations:
    file_ops = create_file_ops()
    if prev_compaction_index >= 0:
        previous = entries[prev_compaction_index]
        if previous.type == "compaction" and isinstance(previous.details, dict):
            details = previous.details
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
    for message in messages:
        extract_file_ops_from_message(message, file_ops)
    return file_ops


def prepare_compaction(
    path_entries: list[Entry],
    settings: CompactionSettings,
) -> CompactionPreparation | None:
    if not path_entries or path_entries[-1].type == "compaction":
        return None

    prev_compaction_index = -1
    for i in range(len(path_entries) - 1, -1, -1):
        if path_entries[i].type == "compaction":
            prev_compaction_index = i
            break

    previous_summary: str | None = None
    compactable_entries = list(path_entries)
    if prev_compaction_index >= 0:
        previous = path_entries[prev_compaction_index]
        previous_summary = previous.summary
        virtual_entries: list[Entry] = []
        for index, message in enumerate(previous.retained_tail or []):
            virtual_entries.append(
                Entry(
                    type="message",
                    id=f"{previous.id}:retained:{index}",
                    parent_id=previous.id if index == 0 else f"{previous.id}:retained:{index - 1}",
                    seq=previous.seq,
                    timestamp=message.get("timestamp", 0) if isinstance(message, dict) else 0,
                    message=message,
                )
            )
        compactable_entries = virtual_entries + list(path_entries[prev_compaction_index + 1 :])

    boundary_end = len(compactable_entries)
    tokens_before = estimate_context_tokens(build_session_context(path_entries)["messages"])["tokens"]

    cut_point = find_cut_point(
        compactable_entries, 0, boundary_end, settings.keep_recent_tokens
    )
    history_end = (
        cut_point.turn_start_index if cut_point.is_split_turn else cut_point.first_kept_entry_index
    )

    messages_to_summarize: list[Message] = []
    for i in range(history_end):
        message = _get_message_from_entry_for_compaction(compactable_entries[i])
        if message is not None:
            messages_to_summarize.append(message)

    turn_prefix_messages: list[Message] = []
    if cut_point.is_split_turn:
        for i in range(cut_point.turn_start_index, cut_point.first_kept_entry_index):
            message = _get_message_from_entry_for_compaction(compactable_entries[i])
            if message is not None:
                turn_prefix_messages.append(message)

    retained_tail: list[Message] = []
    for i in range(cut_point.first_kept_entry_index, boundary_end):
        message = _get_message_from_entry_for_compaction(compactable_entries[i])
        if message is not None:
            retained_tail.append(message)

    file_ops = _extract_file_operations(messages_to_summarize, path_entries, prev_compaction_index)
    if cut_point.is_split_turn:
        for message in turn_prefix_messages:
            extract_file_ops_from_message(message, file_ops)

    return CompactionPreparation(
        messages_to_summarize=messages_to_summarize,
        turn_prefix_messages=turn_prefix_messages,
        retained_tail=retained_tail,
        is_split_turn=cut_point.is_split_turn,
        tokens_before=tokens_before,
        previous_summary=previous_summary,
        file_ops=file_ops,
        settings=settings,
    )
