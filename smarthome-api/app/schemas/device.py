from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DeviceStatus = Literal["online", "offline", "warning", "running"]
DevicePlatform = Literal["Home Assistant", "Matter", "Zigbee", "MQTT"]


class DeviceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DeviceQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=80)
    type: str | None = Field(default=None, max_length=32)
    status: DeviceStatus | None = None
    room: str | None = Field(default=None, max_length=80)


class DeviceCreate(DeviceSchema):
    name: str = Field(min_length=1, max_length=80)
    room: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=32)
    brand: str = Field(min_length=1, max_length=64)
    connection: DevicePlatform
    device_id: str | None = Field(default=None, min_length=1, max_length=64)
    firmware: str = Field(default="1.0.0", min_length=1, max_length=64)
    icon: str = "device-management"
    color: str = Field(default="#6b7280", min_length=1, max_length=16)
    image_url: str | None = Field(default=None, max_length=255)

    @field_validator(
        "name",
        "room",
        "brand",
        "type",
        "device_id",
        "firmware",
        "icon",
        "color",
        "image_url",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class DeviceUpdate(DeviceSchema):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    room: str | None = Field(default=None, min_length=1, max_length=80)
    type: str | None = Field(default=None, min_length=1, max_length=32)
    brand: str | None = Field(default=None, min_length=1, max_length=64)
    status: DeviceStatus | None = None
    connection: DevicePlatform | None = None
    firmware: str | None = Field(default=None, min_length=1, max_length=64)
    icon: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, min_length=1, max_length=16)
    image_url: str | None = Field(default=None, max_length=255)

    @field_validator(
        "name",
        "room",
        "type",
        "brand",
        "firmware",
        "icon",
        "color",
        "image_url",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update_field(self) -> "DeviceUpdate":
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("更新字段不能为 null")
        return self


class DeviceSync(BaseModel):
    platform: DevicePlatform


class DeviceRead(DeviceSchema):
    id: int
    name: str
    room: str
    type: str
    brand: str
    status: DeviceStatus
    connection: DevicePlatform
    firmware: str
    icon: str = "device-management"
    color: str = "#6b7280"
    image_url: str | None
    last_online: datetime | None


class DeviceLogRead(DeviceSchema):
    id: int
    device_id: int
    action: str
    message: str
    created_at: datetime


class DeviceDetailRead(DeviceRead):
    device_id: str
    created_at: datetime
    updated_at: datetime


class DeviceDetailWithLogs(DeviceDetailRead):
    logs: list[DeviceLogRead]


class DeviceListRead(DeviceSchema):
    total: int
    page: int
    page_size: int
    items: list[DeviceRead]


class DeviceLogListRead(DeviceSchema):
    total: int
    page: int
    page_size: int
    items: list[DeviceLogRead]


class DeviceSyncRead(DeviceSchema):
    platform: DevicePlatform
    synced_count: int


class DeviceBatchGroup(BaseModel):
    group: str = Field(min_length=1, max_length=80, description="分组名称")
    device_ids: list[int] = Field(
        default_factory=list, description="分配到该组的设备，为空则创建分组但不分配"
    )

    @field_validator("group", mode="before")
    @classmethod
    def strip_group(cls, value: str) -> str:
        return value.strip()

    @field_validator("device_ids")
    @classmethod
    def unique_device_ids(cls, value: list[int]) -> list[int]:
        if any(device_id <= 0 for device_id in value):
            raise ValueError("device_ids 必须是正整数")
        if len(value) != len(set(value)):
            raise ValueError("device_ids 不能重复")
        return value


class DeviceBatchGroupResult(DeviceSchema):
    group_id: int
    group: str
    assigned_count: int = 0


class DeviceImageRead(DeviceSchema):
    image_url: str
    original_name: str
    mime_type: str
    size_bytes: int
