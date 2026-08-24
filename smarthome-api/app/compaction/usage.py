"""usage 合并与标准化（对应文档 §5.2 / §9 的 usage 计入总账）。"""

from __future__ import annotations

from typing import Any

_USAGE_KEYS = ("input", "output", "cacheRead", "cacheWrite", "totalTokens")


def combine_usage(*usages: dict[str, Any] | None) -> dict[str, Any] | None:
    """把多个摘要请求的 usage 逐项相加（split turn 时合并两次请求的用量）。"""
    non_empty = [usage for usage in usages if isinstance(usage, dict)]
    if not non_empty:
        return None

    combined: dict[str, Any] = {}
    for key in _USAGE_KEYS:
        total = sum(int(usage.get(key, 0) or 0) for usage in non_empty)
        if total:
            combined[key] = total

    cost_total = sum(
        float((usage.get("cost") or {}).get("total", 0) or 0) for usage in non_empty
    )
    if cost_total:
        combined["cost"] = {"total": cost_total}

    return combined or None


def usage_from_metadata(meta: Any) -> dict[str, Any] | None:
    """把 langchain 的 ``usage_metadata`` 标准化为存储层使用的 usage 字典。

    langchain 键为 snake_case（input_tokens / output_tokens / total_tokens），
    存储层（``Record`` / ``CompactionEntry.usage``）使用 camelCase。
    """
    if not isinstance(meta, dict):
        return None

    input_tokens = int(meta.get("input_tokens", meta.get("input", 0)) or 0)
    output_tokens = int(meta.get("output_tokens", meta.get("output", 0)) or 0)
    total_tokens = int(meta.get("total_tokens", meta.get("totalTokens", 0)) or 0)
    if not total_tokens:
        total_tokens = input_tokens + output_tokens

    if not any((input_tokens, output_tokens, total_tokens)):
        return None

    return {
        "input": input_tokens,
        "output": output_tokens,
        "cacheRead": int(meta.get("cache_read_tokens", meta.get("cache_read", 0)) or 0),
        "cacheWrite": int(meta.get("cache_write_tokens", meta.get("cache_write", 0)) or 0),
        "totalTokens": total_tokens,
    }
