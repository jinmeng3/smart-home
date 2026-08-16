from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OverviewSchema(BaseModel):
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


class OverviewSummary(BaseModel):
    device_total: int
    device_online: int
    running_automation_count: int
    alert_count: int = 0
    monthly_energy_kwh: float = 0
    energy_saving_rate: float = 0


class HomeStatus(BaseModel):
    status: str = "normal"
    people_home: int = 0
    temperature: float
    humidity: int
    air_quality: str
    pm25: int
    locked_count: int = 0
    lock_total: int = 0


class OverviewRoom(BaseModel):
    id: int
    name: str
    device_count: int
    light_on: int
    light_total: int
    temperature: float
    device_summaries: list[str]


class OverviewRead(BaseModel):
    summary: OverviewSummary
    home_status: HomeStatus
    rooms: list[OverviewRoom]
    recent_devices: list[dict[str, Any]] = Field(default_factory=list)
    activities: list[dict[str, Any]] = Field(default_factory=list)
    schedule: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class ModeExecuteWrite(OverviewSchema):
    mode: str = Field(pattern="^(home|away|sleep|guest)$")
    room_ids: list[int] = Field(default_factory=list)
    run_automations: bool = True
    idempotency_key: str = Field(min_length=1, max_length=128)


class TaskRead(OverviewSchema):
    id: int
    status: str
    affected_device_count: int | None = None
    checked_count: int | None = None
    device_count: int | None = None
    estimated_seconds: int | None = None


class InspectionWrite(OverviewSchema):
    scope: str = Field(pattern="^(all|rooms|device_types)$")
    room_ids: list[int] = Field(default_factory=list)
    device_types: list[str] = Field(default_factory=list)
    checks: list[str] = Field(min_length=1)


class ScheduleWrite(OverviewSchema):
    enabled: bool = True
    repeat_days: list[int] = Field(default_factory=list)
    targets: dict[str, list[int | str]] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)
    version: int | None = Field(default=None, ge=1)


class ScheduleRead(ScheduleWrite):
    id: int
    schedule_date: date
    version: int
    updated_at: datetime


class SyncJobWrite(OverviewSchema):
    scope: str = "all"
    sources: list[str] = Field(min_length=1)
    options: dict[str, bool] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=128)


class SyncJobRead(OverviewSchema):
    id: int
    status: str
    statistics: dict[str, int] = Field(default_factory=dict)
