from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.schemas.account import AccountRead
from app.schemas.auth import AuthResponse
from app.services.security import register_current_device

DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"invalid-password", bcrypt.gensalt()).decode(
    "utf-8"
)


# === 设备信息工具 ===


def _device_info_from_ua(user_agent: str | None) -> tuple[str, str]:
    """从 User-Agent 推导设备名称和登录位置/平台。"""
    ua = (user_agent or "").lower()
    if any(keyword in ua for keyword in ("mobile", "android", "iphone", "ipad")):
        return "当前设备", "移动设备"
    return "当前设备", "桌面浏览器"

# === Token 工具 ===


def generate_token(
    user_id: int,
    secret_key: str,
    expires_in: int = 3600,
) -> str:
    """生成带用户标识和过期时间的访问令牌。"""
    now = datetime.now(timezone.utc)
    exp_time = now + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "type": "access",
        "iat": now,
        "exp": exp_time,
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def parse_token(
    token: str,
    secret_key: str,
) -> dict:
    """验证访问令牌并返回载荷。"""
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# === 登录注册 ===


def login_service(
    db: Session,
    settings: Settings,
    account: str,
    password: str,
    user_agent: str | None = None,
) -> AuthResponse:
    """校验邮箱和密码，并返回认证结果。"""
    normalized_account = account.casefold()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_account))
    password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_matches = bcrypt.checkpw(
        password.encode("utf-8"), password_hash.encode("utf-8")
    )
    now = datetime.now(timezone.utc)

    if user and user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is unavailable",
        )

    locked_until = user.locked_until if user else None
    if locked_until and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    if user and locked_until and locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Too many failed login attempts. Try again later",
        )

    if not user or not password_matches:
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.max_failed_login_attempts:
                user.locked_until = now + timedelta(seconds=settings.login_lock_seconds)
                user.failed_login_count = 0
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account or password",
        )

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    db.refresh(user)

    # 登录成功后自动注册当前设备
    _device_info = _device_info_from_ua(user_agent)
    register_current_device(db, user, _device_info[0], _device_info[1])

    return AuthResponse(
        access_token=generate_token(
            user_id=user.id,
            expires_in=settings.access_token_expire_seconds,
            secret_key=settings.jwt_secret_key,
        ),
        token_type="Bearer",
        expires_in=settings.access_token_expire_seconds,
        user=AccountRead.model_validate(user),
    )


def register_service(
    db: Session,
    settings: Settings,
    username: str,
    email: str,
    password: str,
) -> AuthResponse:
    """注册用户，数据库唯一约束作为并发场景的最终防线。"""
    normalized_email = email.casefold()
    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    new_user = User(name=username, email=normalized_email, password_hash=password_hash)
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        ) from exc

    db.refresh(new_user)
    return AuthResponse(
        access_token=generate_token(
            user_id=new_user.id,
            expires_in=settings.access_token_expire_seconds,
            secret_key=settings.jwt_secret_key,
        ),
        token_type="Bearer",
        expires_in=settings.access_token_expire_seconds,
        user=AccountRead.model_validate(new_user),
    )
