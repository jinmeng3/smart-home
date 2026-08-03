from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomSchema(BaseModel):
    model_config = ConfigDict(alias_generator=lambda value: value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:]), populate_by_name=True)


class RoomRead(RoomSchema):
    id: int
    name: str
    floor: str
    room_type: str
    image_url: str | None
    area: float
    comfort: int
    temperature: float
    humidity: int
    pm25: int
    illuminance: int
    noise: int
    device_count: int
    online_count: int
    device_states: dict[str, bool | int | str]
    updated_at: datetime


class RoomListRead(RoomSchema):
    items: list[RoomRead]
    total: int


class RoomDeviceWrite(RoomSchema):
    device: str = Field(min_length=1, max_length=40)
    value: bool | int | str


class RoomQuickActionWrite(RoomSchema):
    action: str = Field(pattern="^(all_lights|air_conditioner|curtains)$")

