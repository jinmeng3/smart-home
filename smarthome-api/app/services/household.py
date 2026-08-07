from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import HouseholdMembership
from app.models.user import User


def get_default_household_id(db: Session, user: User) -> int:
    """返回用户最早加入的家庭，供未显式携带家庭ID的兼容接口使用。"""
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前用户尚未加入家庭",
        )
    return household_id
