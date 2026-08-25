import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.core.config import Settings, get_settings
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.account import (
    AccountRead,
    AccountUpdate,
    AvatarResponse,
    UserPreferencesWrite,
)
from app.schemas.common import ApiResponse
from app.services.avatar import delete_avatar_file, save_avatar_file

router = APIRouter(prefix="/account", tags=["account"])
SETTINGS_DEPENDENCY = Depends(get_settings)


# === 账户资料 ===


@router.get("/me", response_model=ApiResponse[AccountRead])
def read_me(current_user: User = CURRENT_USER_DEPENDENCY) -> ApiResponse[AccountRead]:
    """获取当前用户资料。"""
    return ApiResponse(data=current_user)


@router.patch("/me", response_model=ApiResponse[AccountRead])
def update_me(
    payload: AccountUpdate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[AccountRead]:
    """
    更新当前用户的姓名和邮箱。
    """
    if payload.name is not None and payload.name.strip():
        current_user.name = payload.name.strip()

    if payload.email is not None:
        normalized_email = str(payload.email).casefold()
        existing_user = db.scalar(
            select(User).where(
                func.lower(User.email) == normalized_email,
                User.id != current_user.id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="邮箱已被使用"
            )

        current_user.email = normalized_email

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="邮箱已被使用"
        ) from exc
    db.refresh(current_user)
    return ApiResponse(data=current_user)


@router.get("/me/preferences", response_model=ApiResponse[UserPreferencesWrite])
def read_preferences(
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[UserPreferencesWrite]:
    preferences = db.get(UserPreferences, current_user.id)
    if not preferences:
        return ApiResponse(data=UserPreferencesWrite())
    try:
        data = json.loads(preferences.preferences_json)
    except json.JSONDecodeError:
        data = {}
    return ApiResponse(data=UserPreferencesWrite.model_validate(data))


@router.put("/me/preferences", response_model=ApiResponse[UserPreferencesWrite])
def update_preferences(
    payload: UserPreferencesWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[UserPreferencesWrite]:
    preferences = db.get(UserPreferences, current_user.id)
    serialized = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False)
    if preferences:
        preferences.preferences_json = serialized
    else:
        db.add(UserPreferences(user_id=current_user.id, preferences_json=serialized))
    db.commit()
    return ApiResponse(data=payload, message="saved")


# === 头像 ===


@router.post("/me/avatar", response_model=ApiResponse[AvatarResponse])
async def upload_avatar(
    avatar: UploadFile,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[AvatarResponse]:
    """
    上传当前用户头像，并返回新的头像访问地址。
    """
    old_avatar_url = current_user.avatar_url
    avatar_url = await save_avatar_file(settings, avatar)
    current_user.avatar_url = avatar_url
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_avatar_file(settings, avatar_url)
        raise

    delete_avatar_file(settings, old_avatar_url)
    return ApiResponse(data=AvatarResponse(avatar_url=avatar_url), message="created")


@router.delete("/me/avatar", response_model=ApiResponse[AvatarResponse])
def delete_avatar(
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[AvatarResponse]:
    """
    删除当前用户头像，并清空账号中的头像地址。
    """
    old_avatar_url = current_user.avatar_url
    current_user.avatar_url = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    delete_avatar_file(settings, old_avatar_url)
    return ApiResponse(data=AvatarResponse(avatar_url=None))
