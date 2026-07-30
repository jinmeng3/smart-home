from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.ai import (
    AIModelCreate,
    AIModelRead,
    AIModelUpdate,
)

router = APIRouter(prefix="/ai_model", tags=["ai_model"])


def get_current_ai_model(db: Session, current_user: User) -> AIModel:
    model = db.scalar(select(AIModel).where(AIModel.user_id == current_user.id))
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model


@router.get("/model", response_model=AIModelRead)
def read_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> AIModel:
    return get_current_ai_model(db, current_user)


@router.post("/model", response_model=AIModelRead, status_code=status.HTTP_201_CREATED)
def create_ai_model(
    payload: AIModelCreate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> AIModel:
    existing_model = db.scalar(
        select(AIModel).where(AIModel.user_id == current_user.id)
    )
    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Model already exists"
        )

    db_model = AIModel(
        user_id=current_user.id,
        name=payload.name.strip(),
        provider=payload.provider,
        api_endpoint=payload.api_endpoint,
        api_key=payload.api_key,
        parameters={},
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


@router.patch("/model", response_model=AIModelRead)
def update_ai_model(
    payload: AIModelUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> AIModel:
    db_model = db.scalar(select(AIModel).where(AIModel.user_id == current_user.id))
    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    if payload.name is not None and payload.name.strip():
        db_model.name = payload.name.strip()

    if payload.provider is not None:
        db_model.provider = payload.provider

    if payload.api_endpoint is not None:
        db_model.api_endpoint = payload.api_endpoint

    if payload.api_key is not None:
        db_model.api_key = payload.api_key

    if payload.is_active is not None:
        db_model.is_active = payload.is_active

    if payload.description is not None:
        db_model.description = payload.description

    db.commit()
    db.refresh(db_model)
    return db_model


@router.delete("/model", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> Response:
    db_model = db.scalar(select(AIModel).where(AIModel.user_id == current_user.id))
    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    db.delete(db_model)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
