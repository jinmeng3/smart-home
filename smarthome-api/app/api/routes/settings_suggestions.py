from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY, get_model_cache
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.settings_suggestions import AiSuggestionsRead
from app.services.settings_suggestions import generate_ai_suggestions

router = APIRouter(prefix="/settings/suggestions", tags=["settings"])


@router.post("/ai", response_model=ApiResponse[AiSuggestionsRead])
def post_ai_suggestions(
    payload: dict[str, Any],
    force: bool = Query(default=False, description="忽略缓存强制重新生成"),
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AiSuggestionsRead]:
    """调用当前用户的激活 AI 模型，生成设置建议。

    请求体为前端 `SettingsState` 的简化快照（任意 JSON），后端仅用作提示词输入。
    """
    snapshot = payload.get("snapshot") if isinstance(payload, dict) else payload
    if not isinstance(snapshot, dict):
        snapshot = {}

    result = generate_ai_suggestions(
        db=db,
        current_user=current_user,
        settings_snapshot=snapshot,
        model_cache=get_model_cache(),
        force=force,
    )
    return ApiResponse(data=result, message="ok")
