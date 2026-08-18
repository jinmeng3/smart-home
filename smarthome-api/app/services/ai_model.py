from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.crypto import decrypt_api_key, encrypt_api_key
from app.agents.factory import ModelsRegistry
from app.core.config import get_settings
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.ai import (
    AIModelCreate,
    AIModelProviderRead,
    AIModelTestRequest,
    AIModelTestResult,
    AIModelUpdate,
)

# === 模型查询 ===


def read_ai_model_service(db: Session, current_user: User) -> AIModel:
    """获取当前用户启用的模型，不允许回退到其他用户或停用模型。"""
    model = db.scalar(
        select(AIModel).where(
            AIModel.user_id == current_user.id,
            AIModel.is_active.is_(True),
        )
    )
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model


def get_ai_models_service(db: Session, current_user: User) -> list[AIModel]:
    """按启用状态和创建时间列出当前用户的模型。"""
    return list(
        db.scalars(
            select(AIModel)
            .where(AIModel.user_id == current_user.id)
            .order_by(AIModel.is_active.desc(), AIModel.created_at.desc())
        ).all()
    )


def get_owned_ai_model(db: Session, current_user: User, model_id: int) -> AIModel:
    """读取当前用户拥有的指定模型，避免跨用户枚举模型。"""
    model = db.scalar(
        select(AIModel).where(
            AIModel.id == model_id,
            AIModel.user_id == current_user.id,
        )
    )
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model


# === 模型管理 ===


def deactivate_ai_models(db: Session, user_id: int) -> None:
    """保证同一用户最多只有一个启用模型。"""
    db.execute(
        update(AIModel)
        .where(AIModel.user_id == user_id, AIModel.is_active.is_(True))
        .values(is_active=False)
    )


def commit_ai_model(db: Session, model: AIModel) -> AIModel:
    """提交模型变更，并将唯一约束冲突转换为统一 HTTP 错误。"""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Model already exists"
        ) from exc

    db.refresh(model)
    return model


def add_ai_model_service(
    db: Session, current_user: User, payload: AIModelCreate
) -> AIModel:
    """创建模型；新模型启用时自动停用旧模型。"""
    if payload.is_active:
        deactivate_ai_models(db, current_user.id)

    values = payload.model_dump()
    values["api_key"] = encrypt_api_key(values.get("api_key"))
    model = AIModel(user_id=current_user.id, **values)
    db.add(model)
    return commit_ai_model(db, model)


def activate_model_service(db: Session, current_user: User, model_id: int) -> AIModel:
    """将指定模型设为当前用户唯一的启用模型。"""
    model = get_owned_ai_model(db, current_user, model_id)

    deactivate_ai_models(db, current_user.id)
    model.is_active = True
    return commit_ai_model(db, model)


def update_ai_model_service(
    db: Session, current_user: User, payload: AIModelUpdate
) -> AIModel:
    """更新当前模型；没有启用模型时更新该用户最近创建的配置。"""
    model = db.scalar(
        select(AIModel)
        .where(AIModel.user_id == current_user.id)
        .order_by(AIModel.is_active.desc(), AIModel.created_at.desc())
    )
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    values = payload.model_dump(exclude_unset=True)
    if "api_key" in values:
        values["api_key"] = encrypt_api_key(values["api_key"])
    for field, value in values.items():
        setattr(model, field, value)
    return commit_ai_model(db, model)


def update_ai_model_by_id_service(
    db: Session, current_user: User, model_id: int, payload: AIModelUpdate
) -> AIModel:
    """更新当前用户拥有的指定模型。"""
    model = get_owned_ai_model(db, current_user, model_id)
    values = payload.model_dump(exclude_unset=True)
    if "api_key" in values:
        values["api_key"] = encrypt_api_key(values["api_key"])
    if values.pop("is_active", False):
        deactivate_ai_models(db, current_user.id)
        model.is_active = True
    for field, value in values.items():
        setattr(model, field, value)
    return commit_ai_model(db, model)


def delete_ai_model_service(db: Session, current_user: User) -> None:
    """删除当前用户正在使用的模型。"""
    model = read_ai_model_service(db, current_user)
    db.delete(model)
    db.commit()


def delete_ai_model_by_id_service(
    db: Session, current_user: User, model_id: int
) -> None:
    """删除当前用户拥有的指定模型。"""
    model = get_owned_ai_model(db, current_user, model_id)
    db.delete(model)
    db.commit()


# === 测试连接 ===


def test_ai_model_service(
    db: Session, current_user: User, payload: AIModelTestRequest
) -> AIModelTestResult:
    """用前端表单的暂存配置实测模型连通性"""
    import time

    api_key = (payload.api_key or "").strip()

    test_cfg = AIModel(
        user_id=current_user.id,
        name=payload.name,
        provider=payload.provider,
        api=payload.api,
        api_endpoint=payload.api_endpoint,
        api_key=api_key,  # ModelsRegistry.apply_auth 会原样使用
        parameters=payload.parameters or {},
        compat=payload.compat,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )

    try:
        registry = ModelsRegistry(get_settings())
        model = registry.build(test_cfg)
        started = time.perf_counter()
        model.invoke("ping")
        latency_ms = int((time.perf_counter() - started) * 1000)
        return AIModelTestResult(ok=True, latency_ms=latency_ms, message="连接成功")
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        return AIModelTestResult(ok=False, message=detail[:300])


def test_saved_ai_model_service(
    db: Session, current_user: User, model_id: int
) -> AIModelTestResult:
    """使用已保存并解密的凭证测试指定模型。"""
    model = get_owned_ai_model(db, current_user, model_id)

    payload = AIModelTestRequest(
        name=model.name,
        provider=model.provider,
        api=model.api,
        api_endpoint=model.api_endpoint,
        api_key=decrypt_api_key(model.api_key),
        parameters=model.parameters or {},
        compat=model.compat,
        temperature=model.temperature,
        max_tokens=min(model.max_tokens, 8192),
    )
    return test_ai_model_service(db, current_user, payload)


# === 供应商选项 ===


def get_supported_providers_service() -> list[AIModelProviderRead]:
    """返回当前配置支持的供应商列表"""
    settings = get_settings()
    return [
        AIModelProviderRead(id=provider_id)
        for provider_id in settings.supported_ai_providers
    ]
