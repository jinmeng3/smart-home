from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY, SETTINGS_DEPENDENCY
from app.core.config import Settings
from app.models.user import User
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
    """验证账号密码并签发访问令牌。"""
    auth_response = authenticate_user(db, settings, payload.account, payload.password)
    return ApiResponse(data=auth_response)


@router.post("/register", response_model=ApiResponse[AuthResponse])
def register(
    payload: RegisterRequest,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[AuthResponse]:
    """创建用户账号并返回首次登录凭证。"""
    auth_response = register_user(
        db,
        settings,
        payload.username,
        str(payload.email),
        payload.password,
    )
    return ApiResponse(message="created", data=auth_response)


@router.post("/logout", response_model=ApiResponse[None])
def logout(
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[None]:
    """结束客户端登录状态；当前 JWT 由客户端负责清除。"""
    return ApiResponse(message="logged out", data=None)
