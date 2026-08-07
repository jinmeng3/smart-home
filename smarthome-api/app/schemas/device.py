from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DeviceStatus = Literal["online", "offline", "warning", "running"]
DevicePlatform = Literal["Home Assistant", "Matter", "Zigbee", "MQTT"]


class DeviceQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, max_length=80)
    type: str | None = Field(default=None, max_length=32)
    status: DeviceStatus | None = None
    room: str | None = Field(default=None, max_length=80)


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    room: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=32)
    brand: str = Field(min_length=1, max_length=64)
    connection: DevicePlatform
    device_id: str | None = Field(default=None, min_length=1, max_length=64)
    firmware: str = Field(default="1.0.0", min_length=1, max_length=64)
    icon: str = "device-management"
    image_url: str | None = Field(default=None, max_length=255)

    @field_validator(
        "name",
        "room",
        "brand",
        "type",
        "device_id",
        "firmware",
        "icon",
        "image_url",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    room: str | None = Field(default=None, min_length=1, max_length=80)
    type: str | None = Field(default=None, min_length=1, max_length=32)
    brand: str | None = Field(default=None, min_length=1, max_length=64)
    status: DeviceStatus | None = None
    connection: DevicePlatform | None = None
    firmware: str | None = Field(default=None, min_length=1, max_length=64)
    icon: str | None = Field(default=None, min_length=1, max_length=64)
    image_url: str | None = Field(default=None, max_length=255)

    @field_validator(
        "name", "room", "brand", "firmware", "icon", "image_url", mode="before"
    )
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update_field(self) -> "DeviceUpdate":
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        return self


class DeviceSync(BaseModel):
    platform: DevicePlatform


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    room: str
    type: str
    brand: str
    status: DeviceStatus
    connection: DevicePlatform
    firmware: str
    icon: str = "device-management"
    image_url: str | None
    last_online: datetime | None


class DeviceLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class DeviceListRead(BaseModel):
    total: int
    items: list[DeviceRead]


class DeviceLogListRead(BaseModel):
    total: int
    items: list[DeviceLogRead]


class DeviceSyncRead(BaseModel):
    platform: DevicePlatform
    synced_count: int


class DeviceBatchGroup(BaseModel):
    group: str = Field(min_length=1, max_length=80, description="分组名称")
    device_ids: list[int] = Field(
        default=[], description="分配到该组的设备，为空则创建分组但不分配"
    )


class DeviceBatchGroupResult(BaseModel):
    group_id: int
    group: str
    assigned_count: int = 0


class DeviceImageRead(BaseModel):
    image_url: str
    original_name: str
    mime_type: str
    size_bytes: int
