from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import DB_DEPENDENCY, SETTINGS_DEPENDENCY
from app.core.config import Settings
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.common import ApiResponse
from app.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[AuthResponse])
def login(
    payload: LoginRequest,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[AuthResponse]:
    auth_response = authenticate_user(db, settings, payload.account, payload.password)
    return ApiResponse(data=auth_response)


@router.post("/register", response_model=ApiResponse[AuthResponse])
def register(
    payload: RegisterRequest,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[AuthResponse]:
    auth_response = register_user(
        db,
        settings,
        payload.username,
        str(payload.email),
        payload.password,
    )
    return ApiResponse(message="created", data=auth_response)


@router.post("/logout", response_model=ApiResponse[None])
def logout() -> ApiResponse[None]:
    return ApiResponse(message="logged out", data=None)
