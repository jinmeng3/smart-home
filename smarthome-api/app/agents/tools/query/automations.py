import json

from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.core.config import get_settings
from app.models.automation import Automation
from app.services.automation import get_automation as get_automation_service
from app.services.automation import list_automations_service
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListAutomationsInput(BaseModel):
    """列出自动化规则的筛选参数。"""

    keyword: str | None = Field(default=None, max_length=80)
    trigger_type: str | None = Field(default=None, max_length=32)
    enabled: bool | None = None


def list_automations(
    db: Session, context: AgentContext, keyword=None, trigger_type=None, enabled=None
):
    """列出当前家庭的自动化规则，可按关键词、触发类型、启用状态筛选。返回列表含 id、名称、描述、触发类型、启用状态、优先级等。"""
    limit = get_settings().agent_tool_result_max_length
    result = list_automations_service(
        db, context.household_id, keyword, trigger_type, enabled, 1, limit
    )
    return [item.model_dump(mode="json") for item in result.items]


class GetAutomationInput(BaseModel):
    """获取单个自动化规则的参数。automation_id 和 name 至少提供一个。"""

    automation_id: int | None = None
    name: str | None = Field(default=None, max_length=80)


def get_automation(db: Session, context: AgentContext, automation_id=None, name=None):
    """获取指定自动化规则详情（触发器、条件、动作）。automation_id 或 name 至少提供一个，优先按 automation_id 查找。"""
    if automation_id is None and not name:
        raise AgentToolExecutionError("automation_id 或 name 至少提供一个")
    if automation_id is None:
        automation_id = db.scalar(
            select(Automation.id).where(
                Automation.household_id == context.household_id,
                Automation.name == name,
            )
        )
    if automation_id is None:
        raise AgentToolExecutionError("自动化规则不存在")
    try:
        automation = get_automation_service(db, automation_id, context.household_id)
    except HTTPException as exc:
        raise AgentToolExecutionError(str(exc.detail)) from exc

    def parse_config(value: str) -> dict:
        """解析 JSON 配置字符串，返回 dict。"""
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {"config_error": "invalid_json"}
        return parsed if isinstance(parsed, dict) else {"config_error": "not_object"}

    return {
        "id": automation.id,
        "name": automation.name,
        "description": automation.description,
        "trigger_type": automation.trigger_type,
        "enabled": automation.enabled,
        "priority": automation.priority,
        "version": automation.version,
        "triggers": [
            {"type": item.type, "config": parse_config(item.config_json)}
            for item in automation.triggers
        ],
        "conditions": [
            {
                "type": c.type,
                "config": parse_config(c.config_json),
                "position": c.position,
            }
            for c in sorted(automation.conditions, key=lambda c: c.position)
        ],
        "actions": [
            {
                "type": a.type,
                "config": parse_config(a.config_json),
                "position": a.position,
                "device_id": a.device_id,
                "scene_id": a.scene_id,
            }
            for a in sorted(automation.actions, key=lambda a: a.position)
        ],
    }
