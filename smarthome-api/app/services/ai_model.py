from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ai import AIModel
from app.models.user import User
from app.schemas.ai import AIModelCreate, AIModelUpdate

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


def add_ai_model_service(db: Session, current_user: User, payload: AIModelCreate) -> AIModel:
    """创建模型；新模型启用时自动停用旧模型。"""
    if payload.is_active:
        deactivate_ai_models(db, current_user.id)

    model = AIModel(user_id=current_user.id, **payload.model_dump())
    db.add(model)
    return commit_ai_model(db, model)


def activate_model_service(db: Session, current_user: User, model_id: int) -> AIModel:
    """将指定模型设为当前用户唯一的启用模型。"""
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
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    return commit_ai_model(db, model)


def delete_ai_model_service(db: Session, current_user: User) -> None:
    """删除当前用户正在使用的模型。"""
    model = read_ai_model_service(db, current_user)
    db.delete(model)
    db.commit()
