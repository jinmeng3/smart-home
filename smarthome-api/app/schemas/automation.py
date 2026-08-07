from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AutomationSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: (
            value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:])
        ),
        populate_by_name=True,
        from_attributes=True,
    )


class FlowItem(AutomationSchema):
    type: str = Field(min_length=1, max_length=32)
    config: dict[str, Any] = Field(default_factory=dict)


class ConditionWrite(FlowItem):
    position: int | None = Field(default=None, ge=0)


class ActionWrite(FlowItem):
    position: int = Field(ge=0)
    device_id: int | None = None
    scene_id: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "ActionWrite":
        if self.type == "device_command" and self.device_id is None:
            raise ValueError("设备指令必须指定 device_id")
        return self


class AutomationCreate(AutomationSchema):
    name: str = Field(min_length=1, max_length=30)
    description: str = Field(default="", max_length=100)
    enabled: bool = True
    triggers: list[FlowItem] = Field(min_length=1)
    conditions: list[ConditionWrite] = Field(default_factory=list)
    actions: list[ActionWrite] = Field(min_length=1, max_length=50)
    priority: int = Field(default=2, ge=1, le=3)
    cooldown_seconds: int = Field(default=0, ge=0)
    delay_seconds: int = Field(default=0, ge=0)
    note: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def unique_positions(self) -> "AutomationCreate":
        positions = [item.position for item in self.actions]
        if len(positions) != len(set(positions)):
            raise ValueError("动作 position 不能重复")
        return self


class AutomationUpdate(AutomationSchema):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = Field(default=None, max_length=100)
    enabled: bool | None = None
    triggers: list[FlowItem] | None = None
    conditions: list[ConditionWrite] | None = None
    actions: list[ActionWrite] | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    cooldown_seconds: int | None = Field(default=None, ge=0)
    delay_seconds: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=100)
    version: int | None = Field(default=None, ge=1)


class AutomationRead(AutomationSchema):
    id: int
    household_id: int
    name: str
    description: str
    trigger_type: str
    enabled: bool
    device_count: int
    priority: int
    cooldown_seconds: int
    delay_seconds: int
    note: str
    version: int
    triggers: list[FlowItem]
    conditions: list[ConditionWrite]
    actions: list[ActionWrite]
    created_at: datetime
    updated_at: datetime


class AutomationSummary(AutomationSchema):
    enabled: int
    total: int
    running: int
    executions_today: int
    abnormal: int


class AutomationListItem(AutomationSchema):
    id: int
    name: str
    description: str
    trigger_type: str
    enabled: bool
    device_count: int
    updated_at: datetime


class AutomationListRead(AutomationSchema):
    summary: AutomationSummary
    items: list[AutomationListItem]
    total: int


class EnabledWrite(BaseModel):
    enabled: bool


class EnabledRead(BaseModel):
    id: int
    enabled: bool


class ExecuteWrite(BaseModel):
    source: str = Field(default="manual", max_length=32)


class ExecuteRead(AutomationSchema):
    execution_id: int
    status: str


class ExecutionRead(AutomationSchema):
    id: int
    status: str
    source: str
    trigger_snapshot: dict[str, Any]
    duration_ms: int | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class ExecutionListRead(BaseModel):
    total: int
    items: list[ExecutionRead]


class BatchEnableWrite(AutomationSchema):
    rule_ids: list[int] = Field(min_length=1)
    execute_now: bool = False
    execution_interval_seconds: int = Field(default=0, ge=0)


class BatchEnableRead(AutomationSchema):
    updated_count: int
    unchanged_count: int
    execution_batch_id: str | None = None


class BatchScheduleWrite(AutomationSchema):
    rule_ids: list[int] = Field(min_length=1)
    timezone: str = Field(min_length=1, max_length=64)
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")
    weekdays: list[int] = Field(min_length=1)
    frequency: Literal["daily", "weekly"] = "daily"
    interval: int = Field(default=1, ge=1)
