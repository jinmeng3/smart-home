from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.ai import AIModelRead, AIModelUpdate

router = APIRouter(prefix="/ai_model", tags=["ai_model"])


@router.get("/model", response_model=AIModelRead)
def read_ai_model(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    model = db.query(AIModel).filter(AIModel.user_id == current_user.id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model


@router.patch("/model", response_model=AIModelRead)
def update_ai_model(
    model: AIModelUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    db_model = db.query(AIModel).filter(AIModel.user_id == current_user.id).first()
    if not db_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    for key, value in model.model_dump(exclude_unset=True).items():
        setattr(db_model, key, value)

    db.commit()
    db.refresh(db_model)
    return db_model
