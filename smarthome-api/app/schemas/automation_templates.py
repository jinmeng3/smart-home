from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

TriggerTypeLiteral = Literal["schedule", "location", "device", "manual"]
ToneLiteral = Literal["purple", "orange", "green", "blue", "teal", "red", "amber"]


class TemplateAction(BaseModel):
    type: Literal["device_command"] = "device_command"
    position: int = Field(default=0, ge=0)
    deviceId: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    # 语义提示：让前端在创建规则时能从用户设备中匹配真实 device_id。
    # 字段为可选，缺失时前端将该 action 降级为占位。
    device_type: str | None = Field(default=None, max_length=32)
    room: str | None = Field(default=None, max_length=64)


class TemplateTrigger(BaseModel):
    type: TriggerTypeLiteral
    config: dict[str, Any] = Field(default_factory=dict)
    description: str | None = Field(default=None, max_length=128)


class AutomationTemplateItem(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=300)
    trigger_type: TriggerTypeLiteral
    icon: str = Field(min_length=1, max_length=64, default="automation")
    tone: ToneLiteral = "blue"
    device_count: int = Field(ge=1, le=20, default=1)
    triggers: list[TemplateTrigger] = Field(default_factory=list)
    actions: list[TemplateAction] = Field(default_factory=list)


class DeviceSummary(BaseModel):
    """前端传入的设备摘要（不含敏感字段）。"""

    model_config = ConfigDict(extra="allow")

    online: int = 0
    offline: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class AiTemplatesRequest(BaseModel):
    device_summary: DeviceSummary = Field(default_factory=DeviceSummary)
    count: int = Field(default=6, ge=1, le=10)
    force: bool = False


class AiTemplatesRead(BaseModel):
    templates: list[AutomationTemplateItem] = Field(default_factory=list)
    cached: bool = False
