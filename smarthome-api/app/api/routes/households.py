from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
    require_household_admin,
)
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.household import (
    HouseholdCreate,
    HouseholdListItem,
    HouseholdRead,
    HouseholdUpdate,
)

router = APIRouter(prefix="/households", tags=["households"])
HOUSEHOLD_ADMIN_DEPENDENCY = Depends(require_household_admin)


# === 辅助函数 ===


def validate_timezone(timezone: str) -> None:
    """确认时区名称存在于系统 IANA 时区数据库。"""
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="时区无效"
        ) from exc


def serialize_role(role: HouseholdRole | str) -> str:
    """将 ORM 枚举或字符串统一序列化为小写角色值。"""
    value = role.value if isinstance(role, HouseholdRole) else role
    return value.lower()


# === 家庭 CRUD ===


@router.get("", response_model=ApiResponse[list[HouseholdListItem]])
def list_households(
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[list[HouseholdListItem]]:
    """列出当前用户加入的家庭及成员统计。"""
    # 预聚合成员数，避免按家庭逐条查询造成 N+1 问题。
    member_counts = (
        select(
            HouseholdMembership.household_id,
            func.count(HouseholdMembership.id).label("member_count"),
        )
        .group_by(HouseholdMembership.household_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Household,
            HouseholdMembership.role,
            member_counts.c.member_count,
        )
        .join(
            HouseholdMembership,
            HouseholdMembership.household_id == Household.id,
        )
        .join(member_counts, member_counts.c.household_id == Household.id)
        .where(HouseholdMembership.user_id == current_user.id)
        .order_by(Household.updated_at.desc())
    ).all()

    items = [
        HouseholdListItem.model_validate(
            {
                **HouseholdRead.model_validate(household).model_dump(),
                "role": serialize_role(role),
                "member_count": member_count,
            }
        )
        for household, role, member_count in rows
    ]
    return ApiResponse(data=items)


@router.post(
    "", response_model=ApiResponse[HouseholdRead], status_code=status.HTTP_201_CREATED
)
def create_household(
    payload: HouseholdCreate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[HouseholdRead]:
    """创建家庭，并将创建者登记为管理员。"""
    validate_timezone(payload.timezone)
    household = Household(
        name=payload.name.strip(),
        address=payload.address,
        timezone=payload.timezone,
        created_by=current_user.id,
    )

    db.add(household)
    db.flush()
    db.add(
        HouseholdMembership(
            household_id=household.id,
            user_id=current_user.id,
            role=HouseholdRole.ADMIN,
        )
    )
    db.commit()

    db.refresh(household)
    return ApiResponse(data=household, message="created")


@router.get("/{household_id}", response_model=ApiResponse[HouseholdRead])
def read_household(
    membership: HouseholdMembership = HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[HouseholdRead]:
    """读取当前用户有权访问的家庭详情。"""
    household = db.get(Household, membership.household_id)

    if household is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在"
        )

    return ApiResponse(data=household)


@router.patch("/{household_id}", response_model=ApiResponse[HouseholdRead])
def update_household(
    payload: HouseholdUpdate,
    membership: HouseholdMembership = HOUSEHOLD_ADMIN_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[HouseholdRead]:
    """更新家庭资料，仅家庭管理员可操作。"""
    household = db.get(Household, membership.household_id)

    if household is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在"
        )

    if payload.timezone is not None:
        validate_timezone(payload.timezone)
        household.timezone = payload.timezone

    if payload.name is not None and payload.name.strip():
        household.name = payload.name.strip()

    # model_fields_set 用于区分“未传 address”和“显式传 null 清空地址”。
    if "address" in payload.model_fields_set:
        household.address = payload.address

    db.commit()
    db.refresh(household)
    return ApiResponse(data=household)
