from fastapi import APIRouter, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.security import (
    SecurityDeviceRead,
    SecurityDeviceTrustUpdate,
    SecurityLogCreate,
    SecurityLogRead,
    SecurityMetaRead,
)
from app.services.security import (
    create_security_log,
    get_security_meta,
    revoke_device,
    update_device_trust,
)

router = APIRouter(prefix="/account/me/security", tags=["security"])


@router.get("", response_model=ApiResponse[SecurityMetaRead])
def read_security_meta(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SecurityMetaRead]:
    """获取当前用户的安全元数据（登录设备 + 安全日志）。"""
    return ApiResponse(data=get_security_meta(db, current_user))


@router.post(
    "/logs",
    response_model=ApiResponse[SecurityLogRead],
    status_code=status.HTTP_201_CREATED,
)
def add_security_log(
    payload: SecurityLogCreate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SecurityLogRead]:
    """记录一条安全日志。"""
    return ApiResponse(data=create_security_log(db, current_user, payload), message="created")


@router.patch(
    "/devices/{device_id}",
    response_model=ApiResponse[SecurityDeviceRead],
)
def patch_device_trust(
    device_id: int,
    payload: SecurityDeviceTrustUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[SecurityDeviceRead]:
    """更新登录设备信任状态。"""
    return ApiResponse(data=update_device_trust(db, current_user, device_id, payload.trusted))


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_security_device(
    device_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> Response:
    """移除登录设备（当前设备不可移除）。"""
    revoke_device(db, current_user, device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)