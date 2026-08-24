"""消息辅助函数：供上下文投影与压缩摘要复用。"""

from __future__ import annotations

from typing import Any

BRANCH_SUMMARY_PREFIX = "<branch-summary>"
BRANCH_SUMMARY_SUFFIX = "</branch-summary>"
COMPACTION_SUMMARY_PREFIX = "<compaction-summary>"
COMPACTION_SUMMARY_SUFFIX = "</compaction-summary>"


def content_text(content: Any, fallback: str = "") -> str:
    """从字符串或内容块列表提取纯文本。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        return "\n".join(texts) if texts else fallback
    return fallback


def create_branch_summary_message(summary: str, from_id: str, timestamp: int) -> dict[str, Any]:
    return {"role": "branchSummary", "summary": summary, "fromId": from_id, "timestamp": timestamp}


def create_compaction_summary_message(summary: str, tokens_before: int, timestamp: int) -> dict[str, Any]:
    return {
        "role": "compactionSummary",
        "summary": summary,
        "tokensBefore": tokens_before,
        "timestamp": timestamp,
    }
