from __future__ import annotations

import logging
from threading import RLock
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.factory import ModelCache
from app.utils.time import now_timestamp
from app.utils.json import dump_json, extract_json
from app.agents.subagents.domains import SUGGESTIONS_SYSTEM_PROMPT
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.settings_suggestions import (
    AiSuggestionItem,
    AiSuggestionsRead,
    SettingsSectionId,
)

logger = logging.getLogger(__name__)

VALID_SECTIONS: set[str] = set(SettingsSectionId.__args__)

SYSTEM_PROMPT = SUGGESTIONS_SYSTEM_PROMPT

# 简单内存缓存：(user_id, settings_hash) -> (timestamp, payload)
_cache_lock = RLock()
_cache: dict[tuple[int, str], tuple[float, AiSuggestionsRead]] = {}
_CACHE_TTL_SECONDS = 300  # 5 分钟


def _hash_settings(snapshot: dict[str, Any]) -> str:
    """稳定哈希：按 key 排序后 JSON 序列化，避免 dict 顺序差异。"""
    return dump_json(snapshot, sort_keys=True, default=str)




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
    now = now_timestamp()

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
        f"{dump_json(settings_snapshot, indent=2)}\n\n"
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

    parsed = extract_json(str(raw_content))
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
