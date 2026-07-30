from collections.abc import Generator

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db as session_get_db
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    yield from session_get_db()


DB_DEPENDENCY = Depends(get_db)
HOUSEHOLD_ID_PATH = Path(...)


def get_current_user(
    db: Session = DB_DEPENDENCY,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    if x_user_id is None:
        x_user_id = 1

    user = db.get(User, x_user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user


CURRENT_USER_DEPENDENCY = Depends(get_current_user)


def get_membership_query(
    household_id: int, user_id: int
) -> Select[tuple[HouseholdMembership]]:
    return select(HouseholdMembership).where(
        HouseholdMembership.household_id == household_id,
        HouseholdMembership.user_id == user_id,
    )


def get_membership(
    db: Session, household_id: int, user_id: int
) -> HouseholdMembership | None:
    return db.scalar(get_membership_query(household_id, user_id))


def require_household_member(
    household_id: int = HOUSEHOLD_ID_PATH,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> HouseholdMembership:
    household = db.get(Household, household_id)

    if not household:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在")

    membership = get_membership(db, household_id, current_user.id)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该家庭"
        )

    return membership


HOUSEHOLD_MEMBER_DEPENDENCY = Depends(require_household_member)


def require_household_admin(
    membership: HouseholdMembership = HOUSEHOLD_MEMBER_DEPENDENCY,
) -> HouseholdMembership:
    if membership.role != HouseholdRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权管理该家庭"
        )

    return membership


def count_admins(db: Session, household_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(HouseholdMembership)
            .where(
                HouseholdMembership.household_id == household_id,
                HouseholdMembership.role == HouseholdRole.ADMIN,
            ),
        )
        or 0
    )
