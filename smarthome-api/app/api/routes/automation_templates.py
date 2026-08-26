from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY, get_model_cache
from app.models.user import User
from app.schemas.automation_templates import (
    AiTemplatesRead,
    AiTemplatesRequest,
)
from app.schemas.common import ApiResponse
from app.services.automation_templates import generate_ai_templates

router = APIRouter(prefix="/automations/templates", tags=["automations"])


@router.post("/ai", response_model=ApiResponse[AiTemplatesRead])
def post_ai_templates(
    payload: AiTemplatesRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AiTemplatesRead]:
    """调用当前用户的激活 AI 模型，生成自动化模板建议。"""
    result = generate_ai_templates(
        db=db,
        current_user=current_user,
        device_summary=payload.device_summary,
        count=payload.count,
        model_cache=get_model_cache(),
        force=payload.force,
    )
    return ApiResponse(data=result, message="ok")
