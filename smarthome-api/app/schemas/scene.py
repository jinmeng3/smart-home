from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TriggerType = Literal["manual", "schedule", "location", "device"]

# 场景步骤动作枚举：场景执行时真正下发给设备的写操作。
# "noop" 用于“仅展示不操作”场景（如：调试 / 临时停用某个步骤）。
StepAction = Literal["on", "off", "set_temperature", "set_position", "noop"]


class SceneSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: (
            value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:])
        ),
        populate_by_name=True,
        from_attributes=True,
    )

    def model_dump(self, **kwargs):
        """默认使用别名序列化，确保 camelCase 字段名正确输出。"""
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class SceneStepWrite(SceneSchema):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    device_id: str = Field(min_length=1, max_length=120)
    order: int = Field(ge=1)
    # 动作指令：场景执行时真正下发给设备的写操作。
    # 未填时执行器默认为 "on"（向后兼容历史数据）。
    action: StepAction | None = Field(
        default=None, description="动作指令（on / off / set_temperature / set_position / noop）"
    )
    action_value: float | None = Field(
        default=None, ge=0, le=100, description="动作参数（温度 / 开合度 0-100）"
    )


class SceneStepRead(SceneStepWrite):
    id: str


class SceneWrite(SceneSchema):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="home", min_length=1, max_length=64)
    color: str = Field(default="var(--color-primary-600)", min_length=1, max_length=120)
    trigger_type: TriggerType = "manual"
    trigger_label: str = Field(default="手动执行", min_length=1, max_length=255)
    room_labels: list[str] = Field(default_factory=list, max_length=30)
    device_ids: list[str] = Field(default_factory=list, max_length=100)
    enabled: bool = True
    recommended: bool = False
    high_risk: bool | None = None
    steps: list[SceneStepWrite] = Field(default_factory=list, max_length=100)

    @field_validator(
        "name", "description", "icon", "color", "trigger_label", mode="before"
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class SceneRead(SceneSchema):
    id: str
    name: str
    description: str
    icon: str
    color: str
    trigger_type: TriggerType
    trigger_label: str
    room_labels: list[str]
    device_count: int
    enabled: bool
    recommended: bool
    high_risk: bool
    sort_order: int
    source_template_id: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[SceneStepRead]


class SceneListRead(SceneSchema):
    items: list[SceneRead]
    total: int


class SceneEnabledWrite(SceneSchema):
    enabled: bool


class SceneEnabledRead(SceneSchema):
    id: str
    enabled: bool
    updated_at: datetime


class SceneExecuteWrite(SceneSchema):
    confirm_high_risk: bool = False
    source: str = Field(default="manual", min_length=1, max_length=40)


class SceneExecutionStepRead(SceneSchema):
    step_id: str
    status: str
    message: str | None


class SceneExecutionRead(SceneSchema):
    execution_id: str
    scene_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    steps: list[SceneExecutionStepRead]


class SceneCopyWrite(SceneSchema):
    name: str = Field(min_length=1, max_length=80)


class SceneLogRead(SceneSchema):
    id: str
    scene_id: str
    status: str
    source: str
    started_at: datetime
    finished_at: datetime | None
    message: str | None


class SceneLogListRead(SceneSchema):
    items: list[SceneLogRead]


class SceneSummaryRead(SceneSchema):
    enabled: int
    automation: int
    manual: int
    monthly_executions: int
    enabled_rate: float
    automation_rate: float
    manual_rate: float
    monthly_growth_rate: float


class SceneOrderItem(SceneSchema):
    id: str
    sort_order: int


class SceneOrderWrite(SceneSchema):
    items: list[SceneOrderItem] = Field(min_length=1, max_length=200)


class SceneOrderRead(SceneSchema):
    updated: int


class ScenePreviewWrite(SceneSchema):
    source: str = Field(default="manual", min_length=1, max_length=40)


class ScenePreviewStep(SceneSchema):
    step_id: str
    name: str
    device_id: str
    estimated_ms: int
    risk_level: Literal["low", "high"]


class ScenePreviewRead(SceneSchema):
    scene_id: str
    high_risk: bool
    trigger_label: str
    steps: list[ScenePreviewStep]


class SceneTemplateRead(SceneSchema):
    id: str
    name: str
    description: str
    icon: str
    color: str
    trigger_type: TriggerType
    trigger_label: str
    room_labels: list[str]
    device_count: int
    recommended: bool
    category: str
    steps: list[SceneStepRead]


class SceneTemplateListRead(SceneSchema):
    items: list[SceneTemplateRead]


class SceneTemplateUseWrite(SceneSchema):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    enabled: bool = True
    device_mapping: dict[str, str] = Field(default_factory=dict)


class SceneTemplatePreviewStep(SceneSchema):
    name: str
    description: str
    device_id: str
    matched: bool


class SceneTemplatePreviewRead(SceneSchema):
    template_id: str
    matched_device_count: int
    missing_device_count: int
    steps: list[SceneTemplatePreviewStep]


class SceneDraftWrite(SceneWrite):
    name: str = Field(default="未命名场景", min_length=1, max_length=80)


class SceneDraftRead(SceneSchema):
    draft_id: str
    updated_at: datetime


class SceneBatchEnabledWrite(SceneSchema):
    scene_ids: list[str] = Field(
        default_factory=list, description="目标场景 ID 列表，为空则操作全部场景"
    )
    enabled: bool


class SceneBatchEnabledResult(SceneSchema):
    updated_count: int = 0


class SceneBatchScheduleWrite(SceneSchema):
    scene_ids: list[str] = Field(
        default_factory=list, description="目标场景 ID 列表，为空则操作全部场景"
    )
    trigger_type: TriggerType = "schedule"
    trigger_label: str = Field(min_length=1, max_length=255, description="定时触发描述")


class SceneBatchScheduleResult(SceneSchema):
    updated_count: int = 0
