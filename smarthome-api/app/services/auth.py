from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User
from app.schemas.account import AccountRead
from app.schemas.auth import AuthResponse


def generate_token(
    user_id: int,
    secret_key: str,
    expires_in: int = 3600,
) -> str:
    exp_time = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {
        "user_id": user_id,
        "exp": exp_time,
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def authenticate_user(
    db: Session,
    settings: Settings,
    account: str,
    password: str,
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == account))

    if not user or not bcrypt.checkpw(
        password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid account or password",
        )

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


def register_user(
    db: Session,
    settings: Settings,
    username: str,
    email: str,
    password: str,
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    new_user = User(name=username, email=email, password_hash=password_hash)
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
