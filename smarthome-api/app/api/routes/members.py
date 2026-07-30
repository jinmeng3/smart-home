from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
    count_admins,
    require_household_admin,
)
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.user import User
from app.schemas.member import (
    MemberCreate,
    MemberListResponse,
    MemberRead,
    MemberRoleUpdate,
)

router = APIRouter(prefix="/households/{household_id}/members", tags=["members"])
HOUSEHOLD_ADMIN_DEPENDENCY = Depends(require_household_admin)


def member_to_schema(membership: HouseholdMembership) -> MemberRead:
    return MemberRead(
        membership_id=membership.id,
        user_id=membership.user.id,
        name=membership.user.name,
        email=membership.user.email,
        avatar_url=membership.user.avatar_url,
        role=membership.role,
        joined_at=membership.joined_at,
    )


def get_household_membership(
    db: Session, household_id: int, membership_id: int
) -> HouseholdMembership:
    membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.id == membership_id,
            HouseholdMembership.household_id == household_id,
        ),
    )

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")

    return membership


def ensure_not_last_admin(db: Session, membership: HouseholdMembership) -> None:
    if (
        membership.role == HouseholdRole.ADMIN
        and count_admins(db, membership.household_id) <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="家庭必须至少保留一名管理员"
        )


@router.get("", response_model=MemberListResponse)
def list_members(
    household_id: int,
    db: Session = DB_DEPENDENCY,
    _membership: HouseholdMembership = HOUSEHOLD_MEMBER_DEPENDENCY,
) -> MemberListResponse:
    """
    列出指定家庭的所有成员。
    """
    memberships = db.scalars(
        select(HouseholdMembership)
        .where(HouseholdMembership.household_id == household_id)
        .order_by(HouseholdMembership.joined_at),
    ).all()
    items = [member_to_schema(membership) for membership in memberships]
    return MemberListResponse(items=items, total=len(items))


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    household_id: int,
    payload: MemberCreate,
    db: Session = DB_DEPENDENCY,
    _admin: HouseholdMembership = HOUSEHOLD_ADMIN_DEPENDENCY,
) -> MemberRead:
    """
    按邮箱将已有用户添加为家庭成员，仅家庭管理员可操作。
    """
    user = db.scalar(select(User).where(User.email == str(payload.email)))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    existing_membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.household_id == household_id,
            HouseholdMembership.user_id == user.id,
        ),
    )

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="该用户已是家庭成员"
        )

    membership = HouseholdMembership(
        household_id=household_id, user_id=user.id, role=payload.role
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return member_to_schema(membership)


@router.patch("/{membership_id}", response_model=MemberRead)
def update_member_role(
    household_id: int,
    membership_id: int,
    payload: MemberRoleUpdate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
    _admin: HouseholdMembership = HOUSEHOLD_ADMIN_DEPENDENCY,
) -> MemberRead:
    """
    修改家庭成员角色，并确保家庭至少保留一名管理员。
    """
    membership = get_household_membership(db, household_id, membership_id)

    if membership.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能修改自己的角色"
        )

    if payload.role == HouseholdRole.MEMBER:
        ensure_not_last_admin(db, membership)

    membership.role = payload.role
    db.commit()
    db.refresh(membership)
    return member_to_schema(membership)


@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    household_id: int,
    membership_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
    _admin: HouseholdMembership = HOUSEHOLD_ADMIN_DEPENDENCY,
) -> Response:
    """
    移除家庭成员，不能移除自己或家庭最后一名管理员。
    """
    membership = get_household_membership(db, household_id, membership_id)

    if membership.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己"
        )

    ensure_not_last_admin(db, membership)
    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
