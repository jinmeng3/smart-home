from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.device import DeviceStatus


class RoomSchema(BaseModel):
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
    device: list["RoomDeviceListItem"] = Field(default_factory=list)
    device_count: int = Field(default=0, ge=0)
    online_count: int = Field(default=0, ge=0)
    created_at: datetime
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
    device_id: int = Field(gt=0)
    status: DeviceStatus


class RoomQuickActionWrite(RoomSchema):
    action: str = Field(pattern="^(all_lights|air_conditioner|curtains)$")


class RoomInput(RoomSchema):
    name: str = Field(min_length=1, max_length=80)
    floor: str = Field(default="1F", min_length=1, max_length=40)
    room_type: str = Field(default="living", min_length=1, max_length=32)
    icon: str = Field(default="room", min_length=1, max_length=40)
    theme_color: str = Field(default="#3478f6", pattern=r"^#[0-9A-Fa-f]{6}$")
    image_url: str | None = Field(default=None, max_length=500)
    area: float = Field(default=0, ge=0)
    comfort: int = Field(default=80, ge=0, le=100)
    version: int | None = Field(default=None, ge=1)
    device_ids: list[int] = Field(default_factory=list)

    @field_validator("name", "floor", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("device_ids")
    @classmethod
    def unique_device_ids(cls, value: list[int]) -> list[int]:
        if any(device_id <= 0 for device_id in value):
            raise ValueError("设备ID必须为正整数")
        if len(value) != len(set(value)):
            raise ValueError("设备ID不能重复")
        return value


class RoomDeviceBinding(RoomSchema):
    device_id: int = Field(gt=0)
    group: str = Field(default="未分组", min_length=1, max_length=80)
    favorite: bool = False
    sort_order: int = Field(default=0, ge=0)

    @field_validator("group", mode="before")
    @classmethod
    def strip_group(cls, value: str) -> str:
        return value.strip()


class RoomDevicesWrite(RoomSchema):
    devices: list[RoomDeviceBinding]

    @field_validator("devices")
    @classmethod
    def unique_devices(cls, value: list[RoomDeviceBinding]) -> list[RoomDeviceBinding]:
        ids = [item.device_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("设备ID不能重复")
        return value


class RoomDeviceMetaWrite(RoomSchema):
    group: str | None = Field(default=None, max_length=80)
    favorite: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_update_field(self) -> "RoomDeviceMetaWrite":
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("更新字段不能为 null")
        return self


class RoomDeviceListItem(RoomSchema):
    id: int
    name: str
    type: str
    brand: str
    status: str
    icon: str = "device-management"
    color: str = "#6b7280"
    group: str
    favorite: bool
    sort_order: int
    updated_at: datetime


class RoomDeviceListRead(RoomSchema):
    items: list[RoomDeviceListItem]
    total: int


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


class RoomLogListRead(RoomSchema):
    total: int
    page: int
    page_size: int
    items: list[RoomLogRead]


class RoomSceneExecuteWrite(RoomSchema):
    scope: str = Field(default="room", pattern="^(room|all)$")
    sync_automation: bool = True


class RoomEnvironmentLatestRead(RoomSchema):
    sampled_at: datetime
    values: dict[str, float] = Field(default_factory=dict)


class RoomEnvironmentPoint(RoomSchema):
    sampled_at: datetime
    values: dict[str, float] = Field(default_factory=dict)


class RoomEnvironmentTrendRead(RoomSchema):
    metrics: list[str] = Field(default_factory=list)
    items: list[RoomEnvironmentPoint] = Field(default_factory=list)


class RoomEnvironmentReportRead(RoomSchema):
    task_id: str
    status: str
    download_url: str | None = None
