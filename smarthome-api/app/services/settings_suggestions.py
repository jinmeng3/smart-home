from __future__ import annotations

import json
import logging
import re
import time
from threading import RLock
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.factory import ModelCache
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.settings_suggestions import (
    AiSuggestionItem,
    AiSuggestionsRead,
    SettingsSectionId,
)

logger = logging.getLogger(__name__)

VALID_SECTIONS: set[str] = set(SettingsSectionId.__args__)

SYSTEM_PROMPT = """你是智能家居设置中心助手。根据用户当前的设置快照，生成最多 5 条**尚未完成**的设置建议。

要求：
1. 仅输出 JSON，不要任何解释或 Markdown 代码块。
2. JSON 结构必须为：{"suggestions": [{"id": "kebab-case-唯一", "target": "account|appearance|ai|homeAssistant|notifications|security|backup", "title": "<=24字", "description": "<=60字"}]}
3. target 必须是上述七个值之一，否则该条建议会被丢弃。
4. 只列出用户当前**未做**的事项；若用户已正确配置，不要重复建议。
5. 文案简洁、面向行动，避免空话（如"建议优化"）。
6. id 必须以 settings- 前缀，便于前端去重。
"""

# 简单内存缓存：(user_id, settings_hash) -> (timestamp, payload)
_cache_lock = RLock()
_cache: dict[tuple[int, str], tuple[float, AiSuggestionsRead]] = {}
_CACHE_TTL_SECONDS = 300  # 5 分钟


def _hash_settings(snapshot: dict[str, Any]) -> str:
    """稳定哈希：按 key 排序后 JSON 序列化，避免 dict 顺序差异。"""
    return json.dumps(snapshot, sort_keys=True, ensure_ascii=False, default=str)


def _extract_json(content: str) -> dict[str, Any] | None:
    """从模型输出中抠出 JSON。模型偶尔会包 Markdown 块或附加说明。"""
    if not content:
        return None
    text = content.strip()
    # 去掉 ```json ... ``` 包裹
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    # 取第一个完整 JSON 对象
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None
    return None


def _sanitize(raw: dict[str, Any]) -> list[AiSuggestionItem]:
    """过滤掉 target 非法 / 字段缺失 / id 重复 / 长度超限的项。"""
    out: list[AiSuggestionItem] = []
    seen_ids: set[str] = set()
    items = raw.get("suggestions")
    if not isinstance(items, list):
        return out
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        target = raw_item.get("target")
        if target not in VALID_SECTIONS:
            continue
        item_id = str(raw_item.get("id") or "").strip()
        title = str(raw_item.get("title") or "").strip()
        description = str(raw_item.get("description") or "").strip()
        if not item_id or not title or not description:
            continue
        if not item_id.startswith("settings-"):
            item_id = f"settings-{item_id}"
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        out.append(
            AiSuggestionItem(
                id=item_id[:64],
                target=target,  # type: ignore[arg-type]
                title=title[:128],
                description=description[:300],
            )
        )
        if len(out) >= 5:
            break
    return out


def generate_ai_suggestions(
    db: Session,
    current_user: User,
    settings_snapshot: dict[str, Any],
    model_cache: ModelCache,
    *,
    force: bool = False,
) -> AiSuggestionsRead:
    """根据用户 settings 快照调用 LLM，返回结构化建议。

    - 同一 (user_id, settings_hash) 在 5 分钟内复用缓存。
    - 用户没有可用模型时返回 400，前端可降级为本地规则匹配结果。
    """
    settings_hash = _hash_settings(settings_snapshot)
    cache_key = (current_user.id, settings_hash)
    now = time.time()

    if not force:
        with _cache_lock:
            cached = _cache.get(cache_key)
            if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
                payload = cached[1]
                return AiSuggestionsRead(suggestions=payload.suggestions, cached=True)

    model = (
        db.query(AIModel)
        .filter(AIModel.user_id == current_user.id, AIModel.is_active.is_(True))
        .first()
    )
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="尚未配置激活的 AI 模型，无法生成建议",
        )

    user_prompt = (
        "以下是当前用户的设置快照（JSON）：\n"
        f"{json.dumps(settings_snapshot, ensure_ascii=False, indent=2)}\n\n"
        "请按系统提示的 JSON 结构输出建议。"
    )

    try:
        chat_model = model_cache.get(model)
        from langchain_core.messages import HumanMessage, SystemMessage

        response = chat_model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
        )
    except Exception as exc:
        # LLM 调用可能抛出任意异常，统一归一化为 HTTP 502。
        logger.exception("AI 建议生成失败")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 建议生成失败: {exc.__class__.__name__}",
        ) from exc

    raw_content = getattr(response, "content", "") or ""
    if isinstance(raw_content, list):
        # 某些 provider 返回 content blocks
        raw_content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )

    parsed = _extract_json(str(raw_content))
    if not parsed:
        logger.warning("AI 建议返回非 JSON: %r", raw_content[:200])
        return AiSuggestionsRead(suggestions=[], cached=False)

    items = _sanitize(parsed)
    payload = AiSuggestionsRead(suggestions=items, cached=False)

    with _cache_lock:
        # 只在 size 上限内缓存，防止内存膨胀
        if len(_cache) >= 256:
            _cache.pop(next(iter(_cache)))
        _cache[cache_key] = (now, payload)

    return payload
