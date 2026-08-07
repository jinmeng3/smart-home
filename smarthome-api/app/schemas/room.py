from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: (
            value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:])
        ),
        populate_by_name=True,
    )


class RoomRead(RoomSchema):
    id: int
    name: str
    floor: str
    room_type: str
    image_url: str | None
    icon: str = "room"
    theme_color: str = "#3478f6"
    version: int = 1
    area: float
    comfort: int
    device_count: int
    online_count: int
    updated_at: datetime


class RoomDetailRead(RoomSchema):
    """房间详情（包含最近活动和当前场景）"""

    room: RoomRead
    current_scene: str | None = None
    recent_activity: str | None = None
    recent_activity_time: str | None = None


class RoomStatsRead(RoomSchema):
    """房间统计概览"""

    room_count: int
    room_count_change: int = 0  # 较上月变化
    online_rate: float = 0.0  # 在线率百分比
    alert_count: int = 0  # 报警次数
    pending_alert_count: int = 0  # 待处理报警次数


class RoomListRead(RoomSchema):
    items: list[RoomRead]
    total: int


class RoomDeviceWrite(RoomSchema):
    device: str = Field(min_length=1, max_length=40)
    value: bool | int | str


class RoomQuickActionWrite(RoomSchema):
    action: str = Field(pattern="^(all_lights|air_conditioner|curtains)$")


class RoomInput(RoomSchema):
    name: str = Field(min_length=1, max_length=80)
    floor: str = Field(default="1F", min_length=1, max_length=40)
    room_type: str = Field(default="living", min_length=1, max_length=32)
    icon: str = Field(default="room")
    theme_color: str = Field(default="#3478f6", pattern=r"^#[0-9A-Fa-f]{6}$")
    device_ids: list[int] = Field(default_factory=list)

    @field_validator("name", "floor", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class RoomDeviceBinding(RoomSchema):
    device_id: int
    group: str = Field(default="未分组", max_length=80)
    favorite: bool = False
    sort_order: int = Field(default=0, ge=0)


class RoomDevicesWrite(BaseModel):
    devices: list[RoomDeviceBinding]


class RoomDeviceMetaWrite(RoomSchema):
    group: str | None = Field(default=None, max_length=80)
    favorite: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class RoomDeviceListItem(RoomSchema):
    id: int
    name: str
    type: str
    brand: str
    status: str
    group: str
    favorite: bool
    sort_order: int


class RoomDeviceListRead(BaseModel):
    items: list[RoomDeviceListItem]
    total: int


class RoomBatchControlWrite(RoomSchema):
    device_ids: list[int] = Field(min_length=1)
    action: str = Field(pattern="^(turn_on|turn_off)$")


class RoomLogRead(RoomSchema):
    id: int
    occurred_at: datetime
    source: str
    event: str
    result: str
    duration_ms: int | None
    device_id: int | None
    device_name: str | None
    tags: list[str]
    detail: dict[str, Any]


class RoomLogListRead(BaseModel):
    total: int
    items: list[RoomLogRead]


class EnvironmentLatestRead(BaseModel):
    """房间最新环境指标，values 为指标名到数值的映射。"""

    sampled_at: datetime
    values: dict[str, float]


class EnvironmentPoint(RoomSchema):
    sampled_at: datetime
    values: dict[str, float]


class EnvironmentTrendRead(BaseModel):
    metrics: list[str]
    items: list[EnvironmentPoint]


class EnvironmentReportRead(RoomSchema):
    task_id: str
    status: str
    download_url: str | None = None


class RoomSceneExecuteWrite(RoomSchema):
    scope: str = Field(default="room", pattern="^(room|all)$")
    sync_automation: bool = True
