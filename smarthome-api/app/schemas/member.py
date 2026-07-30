from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.membership import HouseholdRole


class MemberCreate(BaseModel):
    email: EmailStr
    role: HouseholdRole = HouseholdRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: HouseholdRole


class MemberRead(BaseModel):
    membership_id: int
    user_id: int
    name: str
    email: EmailStr
    avatar_url: str | None
    role: HouseholdRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    items: list[MemberRead]
    total: int
