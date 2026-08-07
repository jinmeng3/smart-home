from collections.abc import Generator

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db as session_get_db
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.user import User
from app.services.auth import parse_token


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI 依赖）。"""
    yield from session_get_db()


DB_DEPENDENCY = Depends(get_db)
HOUSEHOLD_ID_PATH = Path(...)
SETTINGS_DEPENDENCY = Depends(get_settings)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
OAUTH2_SCHEME_DEPENDENCY = Depends(oauth2_scheme)


def get_current_user(
    token: str = OAUTH2_SCHEME_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> User:
    """解析访问令牌并加载当前用户。"""
    payload = parse_token(token, settings.jwt_secret_key)
    user_id = payload.get("user_id")
    if not isinstance(user_id, int) or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


CURRENT_USER_DEPENDENCY = Depends(get_current_user)


def get_membership_query(
    household_id: int, user_id: int
) -> Select[tuple[HouseholdMembership]]:
    """构建家庭成员关系的查询条件。"""
    return select(HouseholdMembership).where(
        HouseholdMembership.household_id == household_id,
        HouseholdMembership.user_id == user_id,
    )


def get_membership(
    db: Session, household_id: int, user_id: int
) -> HouseholdMembership | None:
    """查询家庭成员关系，不存在时返回 None。"""
    return db.scalar(get_membership_query(household_id, user_id))


def require_household_member(
    household_id: int = HOUSEHOLD_ID_PATH,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> HouseholdMembership:
    """确认当前用户属于路径指定的家庭。"""
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
    """在成员校验基础上继续确认管理员权限。"""
    if membership.role != HouseholdRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权管理该家庭"
        )

    return membership


def count_admins(db: Session, household_id: int) -> int:
    """统计家庭中管理员的剩余数量。"""
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
