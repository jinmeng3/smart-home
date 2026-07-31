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
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/ai_model", tags=["ai_model"])


def get_current_ai_model(db: Session, current_user: User) -> AIModel:
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


@router.get("/models", response_model=ApiResponse[list[AIModelRead]])
def list_ai_models(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[AIModelRead]]:
    models = db.scalars(
        select(AIModel)
        .where(AIModel.user_id == current_user.id)
        .order_by(AIModel.is_active.desc(), AIModel.created_at.desc())
    ).all()
    return ApiResponse(data=list(models))


@router.get("/model", response_model=ApiResponse[AIModelRead])
def read_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    return ApiResponse(data=get_current_ai_model(db, current_user))


@router.post(
    "/model",
    response_model=ApiResponse[AIModelRead],
    status_code=status.HTTP_201_CREATED,
)
def create_ai_model(
    payload: AIModelCreate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    db_model = AIModel(
        user_id=current_user.id,
        name=payload.name.strip(),
        provider=payload.provider,
        api_endpoint=payload.api_endpoint,
        api_key=payload.api_key,
        parameters=payload.parameters,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        is_active=payload.is_active,
        description=payload.description,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return ApiResponse(data=db_model, message="created")


@router.post("/models/{model_id}/activate", response_model=ApiResponse[AIModelRead])
def activate_ai_model(
    model_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    db_model = db.scalar(
        select(AIModel).where(
            AIModel.id == model_id,
            AIModel.user_id == current_user.id,
        )
    )
    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    for model in db.scalars(
        select(AIModel).where(AIModel.user_id == current_user.id)
    ):
        model.is_active = model.id == db_model.id

    db.commit()
    db.refresh(db_model)
    return ApiResponse(data=db_model)


@router.patch("/model", response_model=ApiResponse[AIModelRead])
def update_ai_model(
    payload: AIModelUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[AIModelRead]:
    db_model = db.scalar(select(AIModel).where(AIModel.user_id == current_user.id))
    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    if payload.name is not None and payload.name.strip():
        db_model.name = payload.name.strip()

    if payload.provider is not None:
        db_model.provider = payload.provider.strip()

    if payload.api_endpoint is not None:
        db_model.api_endpoint = payload.api_endpoint.strip()

    if payload.api_key is not None:
        db_model.api_key = payload.api_key.strip()

    if payload.parameters is not None:
        db_model.parameters = payload.parameters

    if payload.temperature is not None:
        db_model.temperature = payload.temperature

    if payload.max_tokens is not None:
        db_model.max_tokens = payload.max_tokens

    if payload.is_active is not None:
        db_model.is_active = payload.is_active

    if payload.description is not None:
        db_model.description = payload.description

    db.commit()
    db.refresh(db_model)
    return ApiResponse(data=db_model)


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
