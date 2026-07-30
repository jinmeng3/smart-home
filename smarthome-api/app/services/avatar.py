from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

extension_by_type = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def avatar_path_from_url(settings: Settings, avatar_url: str | None) -> Path | None:
    if not avatar_url:
        return None

    filename = Path(avatar_url).name
    return settings.avatar_dir / filename


def delete_avatar_file(settings: Settings, avatar_url: str | None) -> None:
    avatar_path = avatar_path_from_url(settings, avatar_url)

    if avatar_path and avatar_path.exists():
        avatar_path.unlink()


async def save_avatar_file(settings: Settings, upload: UploadFile) -> str:
    if upload.content_type not in settings.allowed_avatar_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="不支持该头像格式")

    content = await upload.read()

    if len(content) > settings.max_avatar_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="头像文件过大")

    settings.avatar_dir.mkdir(parents=True, exist_ok=True)
    extension = extension_by_type[upload.content_type]
    filename = f"{uuid4().hex}{extension}"
    avatar_path = settings.avatar_dir / filename
    avatar_path.write_bytes(content)
    return f"/uploads/avatars/{filename}"
