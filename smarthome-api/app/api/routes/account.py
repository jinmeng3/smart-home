from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.account import AccountRead, AccountUpdate, AvatarResponse
from app.schemas.common import ApiResponse
from app.services.avatar import delete_avatar_file, save_avatar_file

router = APIRouter(prefix="/account", tags=["account"])
SETTINGS_DEPENDENCY = Depends(get_settings)


@router.get("/me", response_model=ApiResponse[AccountRead])
def read_me(current_user: User = CURRENT_USER_DEPENDENCY) -> ApiResponse[AccountRead]:
    """
    获取当前用户资料。

    """
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
        existing_user = db.scalar(
            select(User).where(
                User.email == str(payload.email), User.id != current_user.id
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="邮箱已被使用"
            )

        current_user.email = str(payload.email)

    db.commit()
    db.refresh(current_user)
    return ApiResponse(data=current_user)


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
    avatar_url = await save_avatar_file(settings, avatar)
    delete_avatar_file(settings, current_user.avatar_url)
    current_user.avatar_url = avatar_url
    db.commit()
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
    delete_avatar_file(settings, current_user.avatar_url)
    current_user.avatar_url = None
    db.commit()
    return ApiResponse(data=AvatarResponse(avatar_url=None))
