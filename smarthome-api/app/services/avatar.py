from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

EXTENSION_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


# === 头像 ===


def delete_avatar_file(settings: Settings, avatar_url: str | None) -> None:
    """删除应用管理的头像文件；文件不存在时保持幂等。"""
    avatar_path = settings.avatar_dir / Path(avatar_url).name if avatar_url else None

    if avatar_path and avatar_path.exists():
        avatar_path.unlink()


async def save_avatar_file(settings: Settings, upload: UploadFile) -> str:
    """校验头像类型和大小后保存，并返回静态资源地址。"""
    extension = EXTENSION_BY_TYPE.get(upload.content_type or "")
    if upload.content_type not in settings.allowed_avatar_types or not extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="不支持该头像格式",
        )

    content = await upload.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件不能为空"
        )

    if len(content) > settings.max_avatar_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="头像文件过大"
        )

    settings.avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    avatar_path = settings.avatar_dir / filename
    avatar_path.write_bytes(content)
    return f"/uploads/avatars/{filename}"
