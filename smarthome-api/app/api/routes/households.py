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
from app.schemas.household import (
    HouseholdCreate,
    HouseholdListItem,
    HouseholdRead,
    HouseholdUpdate,
)

router = APIRouter(prefix="/households", tags=["households"])
HOUSEHOLD_ADMIN_DEPENDENCY = Depends(require_household_admin)


def validate_timezone(timezone: str) -> None:
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="时区无效"
        ) from exc


def serialize_role(role: HouseholdRole | str) -> str:
    value = role.value if isinstance(role, HouseholdRole) else role
    return value.lower()


@router.get("", response_model=list[HouseholdListItem])
def list_households(
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> list[HouseholdListItem]:
    """
    列出当前用户加入的家庭，包含用户角色和成员数量。
    """
    current_memberships = db.scalars(
        select(HouseholdMembership).where(
            HouseholdMembership.user_id == current_user.id
        )
    ).all()
    rows = []

    for membership in current_memberships:
        household = db.get(Household, membership.household_id)
        member_count = (
            db.scalar(
                select(func.count())
                .select_from(HouseholdMembership)
                .where(HouseholdMembership.household_id == membership.household_id),
            )
            or 0
        )
        rows.append((household, membership.role, member_count))

    return [
        HouseholdListItem.model_validate(
            {
                **HouseholdRead.model_validate(household).model_dump(),
                "role": serialize_role(role),
                "member_count": member_count,
            }
        )
        for household, role, member_count in rows
    ]


@router.post("", response_model=HouseholdRead, status_code=status.HTTP_201_CREATED)
def create_household(
    payload: HouseholdCreate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> Household:
    """
    创建家庭，并将当前用户设为该家庭管理员。
    """
    validate_timezone(payload.timezone)
    household = Household(
        name=payload.name.strip(),
        address=payload.address,
        timezone=payload.timezone,
        created_by=current_user.id,
    )

    try:
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
    except Exception:
        db.rollback()
        raise

    db.refresh(household)
    return household


@router.get("/{household_id}", response_model=HouseholdRead)
def read_household(
    membership: HouseholdMembership = HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> Household:
    """
    获取当前用户已加入家庭的详细信息。
    """
    household = db.get(Household, membership.household_id)

    # 显式处理 None，满足类型检查器。
    if household is None:
        raise HTTPException(status_code=404, detail="家庭不存在")

    return household


@router.patch("/{household_id}", response_model=HouseholdRead)
def update_household(
    payload: HouseholdUpdate,
    membership: HouseholdMembership = HOUSEHOLD_ADMIN_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> Household:
    """
    更新家庭名称、地址或时区，仅家庭管理员可操作。
    """
    household = db.get(Household, membership.household_id)

    if household is None:
        raise HTTPException(status_code=404, detail="家庭不存在")

    if payload.timezone is not None:
        validate_timezone(payload.timezone)
        household.timezone = payload.timezone

    if payload.name is not None and payload.name.strip():
        household.name = payload.name.strip()

    if payload.address is not None:
        household.address = payload.address

    db.commit()
    db.refresh(household)
    return household
