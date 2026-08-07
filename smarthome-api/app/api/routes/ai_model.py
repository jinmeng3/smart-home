from fastapi import APIRouter, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.user import User
from app.schemas.ai import AIModelCreate, AIModelRead, AIModelUpdate
from app.schemas.common import ApiResponse
from app.services.ai_model import (
    activate_model_service,
    add_ai_model_service,
    delete_ai_model_service,
    get_ai_models_service,
    read_ai_model_service,
    update_ai_model_service,
)

router = APIRouter(prefix="/ai_model", tags=["ai_model"])


# === 模型查询 ===


@router.get("/models", response_model=ApiResponse[list[AIModelRead]])
def get_ai_models(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[AIModelRead]]:
    """列出当前用户配置的全部 AI 模型。"""
    return ApiResponse(data=get_ai_models_service(db, current_user))


@router.get("/model", response_model=ApiResponse[AIModelRead])
def read_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    """获取当前用户正在启用的 AI 模型。"""
    return ApiResponse(data=read_ai_model_service(db, current_user))


# === 模型管理 ===


@router.post(
    "/model",
    response_model=ApiResponse[AIModelRead],
    status_code=status.HTTP_201_CREATED,
)
def add_ai_model(
    payload: AIModelCreate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    """创建 AI 模型配置。"""
    return ApiResponse(
        data=add_ai_model_service(db, current_user, payload), message="created"
    )


@router.post("/models/{model_id}/activate", response_model=ApiResponse[AIModelRead])
def activate_model(
    model_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    """将指定模型设为当前启用模型。"""
    return ApiResponse(data=activate_model_service(db, current_user, model_id))


@router.patch("/model", response_model=ApiResponse[AIModelRead])
def update_ai_model(
    payload: AIModelUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    """更新当前启用模型的配置。"""
    return ApiResponse(data=update_ai_model_service(db, current_user, payload))


@router.delete("/model", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> Response:
    """删除当前启用的 AI 模型。"""
    delete_ai_model_service(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
