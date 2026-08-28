"""会话消息序列化：把内部消息转成纯文本，供摘要请求使用（对应文档 §8.2）。

关键目的：让模型把这段内容当作"待总结的素材"而不是"要接下去的对话"。
工具结果（尤其是 read / bash 输出）通常是上下文的最大占用者，超长内容会被
截断到 ``TOOL_RESULT_MAX_CHARS``，保证摘要请求本身不爆 token。
"""

from __future__ import annotations

from typing import Any

from app.session_tree.session.types import Message
from app.utils.json import dump_json

TOOL_RESULT_MAX_CHARS = 2000
_TRUNCATION_SUFFIX = "... [{} more characters truncated]"


def _content_text(content: Any) -> str:
    """从字符串或内容块列表提取纯文本；图片块用占位符表示。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif block.get("type") == "image":
                parts.append("[image]")
        return "\n".join(parts)
    return ""


def _content_blocks(content: Any) -> list[dict[str, Any]]:
    """归一化 assistant 内容块列表。"""
    if isinstance(content, list):
        return [block for block in content if isinstance(block, dict)]
    return []


def truncate_tool_result(text: str, max_chars: int = TOOL_RESULT_MAX_CHARS) -> str:
    """超长工具结果保留开头 ``max_chars`` 字符并追加截断标记。"""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars] + _TRUNCATION_SUFFIX.format(len(text) - max_chars)


def _format_tool_call(name: Any, arguments: Any) -> str:
    name = str(name or "unknown")
    if isinstance(arguments, dict):
        args = ", ".join(
            f"{key}={dump_json(value)}"
            for key, value in arguments.items()
        )
        return f"{name}({args})"
    if arguments is None:
        return f"{name}()"
    return f"{name}({arguments})"


def _serialize_message(message: Message, tool_result_max_chars: int) -> list[str]:
    """把单条内部消息序列化为一行或多行文本。"""
    role = message.get("role") if isinstance(message, dict) else None
    lines: list[str] = []

    if role == "user":
        lines.append(f"[User]: {_content_text(message.get('content'))}")
    elif role == "assistant":
        for block in _content_blocks(message.get("content")):
            block_type = block.get("type")
            if block_type == "text":
                lines.append(f"[Assistant]: {block.get('text', '')}")
            elif block_type == "thinking":
                lines.append(f"[Assistant thinking]: {block.get('thinking', '')}")
            elif block_type == "toolCall":
                lines.append(
                    "[Assistant tool calls]: "
                    f"{_format_tool_call(block.get('name'), block.get('arguments'))}"
                )
    elif role == "toolResult":
        lines.append(
            f"[Tool result]: {truncate_tool_result(_content_text(message.get('content')), tool_result_max_chars)}"
        )
    elif role == "bashExecution":
        lines.append(f"[Bash execution]: command={message.get('command', '')}")
        output = truncate_tool_result(message.get("output") or "", tool_result_max_chars)
        lines.append(f"[Bash output]: {output}")
    elif role == "custom":
        lines.append(f"[Custom]: {_content_text(message.get('content'))}")
    elif role == "branchSummary":
        lines.append(f"[Branch summary]: {message.get('summary', '')}")
    elif role == "compactionSummary":
        lines.append(f"[Compaction summary]: {message.get('summary', '')}")
    return lines


def serialize_conversation(
    messages: list[Message],
    *,
    tool_result_max_chars: int = TOOL_RESULT_MAX_CHARS,
) -> str:
    """把消息列表序列化为纯文本（``[Role]: ...`` 形式）。

    等价于文档 §8.2 中 ``serializeConversation(convertToLlm(messages))`` 的两步：
    先把内部角色投影成可读文本，再拼成一段"素材"。
    """
    lines: list[str] = []
    for message in messages:
        lines.extend(_serialize_message(message, tool_result_max_chars))
    return "\n".join(lines)
