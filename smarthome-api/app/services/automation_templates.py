
from __future__ import annotations

import json
import logging
from threading import RLock
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.utils.time import now_timestamp
from app.utils.json import dump_json, extract_json
from app.agents.factory import ModelCache
from app.agents.subagents.domains import AUTOMATION_TEMPLATES_SYSTEM_PROMPT
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.automation_templates import (
    AiTemplatesRead,
    AutomationTemplateItem,
    DeviceSummary,
    TemplateAction,
    TemplateTrigger,
    ToneLiteral,
    TriggerTypeLiteral,
)

logger = logging.getLogger(__name__)

VALID_TRIGGERS: set[str] = set(TriggerTypeLiteral.__args__)
VALID_TONES: set[str] = set(ToneLiteral.__args__)

# 触发表 → 前端 icon / tone 的合理范围（与前端 TRIGGER_TYPE_MAP 对齐）
_TRIGGER_DEFAULTS: dict[str, dict] = {
    "schedule": {"icon": "clock", "tone": "orange"},
    "location": {"icon": "home", "tone": "green"},
    "device": {"icon": "automation", "tone": "blue"},
    "manual": {"icon": "automation", "tone": "teal"},
}

SYSTEM_PROMPT = AUTOMATION_TEMPLATES_SYSTEM_PROMPT

# 简单内存缓存：(user_id, summary_hash, count) -> (timestamp, payload)
_cache_lock = RLock()
_cache: dict[tuple[int, str, int], tuple[float, AiTemplatesRead]] = {}
_CACHE_TTL_SECONDS = 600  # 10 分钟


def _hash_summary(summary: DeviceSummary) -> str:
    return json.dumps(
        {
            "online": summary.online,
            "offline": summary.offline,
            "by_type": dict(sorted(summary.by_type.items())),
        },
        sort_keys=True,
        ensure_ascii=False,
    )




def _sanitize_trigger(raw: dict) -> TemplateTrigger | None:
    t = raw.get("type")
    if t not in VALID_TRIGGERS:
        return None
    raw_config = raw.get("config")
    config: dict[str, Any] = raw_config if isinstance(raw_config, dict) else {}
    desc = raw.get("description")
    if not isinstance(desc, str) or not desc.strip():
        desc = None
    else:
        desc = desc.strip()[:128]
    return TemplateTrigger(type=t, config=config, description=desc)


def _sanitize_action(raw: dict, position: int) -> TemplateAction:
    raw_config = raw.get("config")
    config: dict[str, Any] = raw_config if isinstance(raw_config, dict) else {}
    device_id = raw.get("deviceId")
    if not isinstance(device_id, int):
        device_id = None
    device_type = raw.get("device_type")
    if not isinstance(device_type, str) or not device_type.strip():
        device_type = None
    else:
        device_type = device_type.strip()[:32]
    room = raw.get("room")
    if (
        not isinstance(room, str)
        or not room.strip()
        or room.strip().lower() in {"null", "none", "any", "all", "全部"}
    ):
        room = None
    else:
        room = room.strip()[:64]
    return TemplateAction(
        position=position,
        deviceId=device_id,
        config=config,
        device_type=device_type,
        room=room,
    )


def _sanitize(raw: dict) -> list[AutomationTemplateItem]:
    out: list[AutomationTemplateItem] = []
    seen_names: set[str] = set()
    items = raw.get("templates")
    if not isinstance(items, list):
        return out
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        name = str(raw_item.get("name") or "").strip()
        description = str(raw_item.get("description") or "").strip()
        trigger_type = raw_item.get("trigger_type")
        icon = str(raw_item.get("icon") or "").strip().lower()
        tone = raw_item.get("tone")
        device_count = raw_item.get("device_count")
        if (
            not name
            or not description
            or trigger_type not in VALID_TRIGGERS
            or tone not in VALID_TONES
            or not icon
        ):
            continue
        if not isinstance(device_count, int) or device_count < 1:
            device_count = 1
        if name in seen_names:
            continue
        seen_names.add(name)

        triggers_raw = raw_item.get("triggers") or []
        actions_raw = raw_item.get("actions") or []
        if not isinstance(triggers_raw, list) or not isinstance(actions_raw, list):
            continue
        triggers = [t for t in (_sanitize_trigger(r) for r in triggers_raw) if t]
        actions = [
            _sanitize_action(r, idx) for idx, r in enumerate(actions_raw)
        ]
        if not triggers or not actions:
            # 兜底：保证至少有一个可用的 trigger + action
            fallback_icon = _TRIGGER_DEFAULTS[trigger_type]["icon"]
            if not icon:
                icon = fallback_icon
            triggers = [TemplateTrigger(type=trigger_type, config={})]
            actions = [TemplateAction(position=0, config={})]

        out.append(
            AutomationTemplateItem(
                name=name[:64],
                description=description[:300],
                trigger_type=trigger_type,
                icon=icon[:64],
                tone=tone,
                device_count=min(max(device_count, 1), 20),
                triggers=triggers,
                actions=actions,
            )
        )
        if len(out) >= 10:
            break
    return out


def generate_ai_templates(
    db: Session,
    current_user: User,
    device_summary: DeviceSummary,
    count: int,
    model_cache: ModelCache,
    *,
    force: bool = False,
) -> AiTemplatesRead:
    """根据用户家庭设备构成调用 LLM 生成 N 条自动化模板。

    - 同一 (user, device_summary_hash) 10 分钟内复用缓存。
    - 用户无激活模型时返回 400；LLM 错误返回 502。
    """
    summary_hash = _hash_summary(device_summary)
    cache_key = (current_user.id, summary_hash, count)
    now = now_timestamp()

    if not force:
        with _cache_lock:
            cached = _cache.get(cache_key)
            if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
                payload = cached[1]
                return AiTemplatesRead(templates=payload.templates, cached=True)

    model = db.query(AIModel).filter(
        AIModel.user_id == current_user.id, AIModel.is_active.is_(True)
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="尚未配置激活的 AI 模型，无法生成模板",
        )

    user_prompt = (
        f"请生成 {count} 条自动化模板。\n\n"
        f"用户家庭设备摘要：\n{dump_json(device_summary.model_dump(), indent=2)}\n\n"
        "按系统提示的 JSON 结构输出。"
    )

    try:
        chat_model = model_cache.get(model)
        from langchain_core.messages import HumanMessage, SystemMessage

        response = chat_model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
        )
    except Exception as exc:
        logger.exception("AI 模板生成失败")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 模板生成失败: {exc.__class__.__name__}",
        ) from exc

    raw_content = getattr(response, "content", "") or ""
    if isinstance(raw_content, list):
        raw_content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )

    parsed = extract_json(str(raw_content))
    if not parsed:
        logger.warning("AI 模板返回非 JSON: %r", raw_content[:200])
        return AiTemplatesRead(templates=[], cached=False)

    items = _sanitize(parsed)[:count]
    payload = AiTemplatesRead(templates=items, cached=False)

    with _cache_lock:
        if len(_cache) >= 256:
            _cache.pop(next(iter(_cache)))
        _cache[cache_key] = (now, payload)

    return payload
