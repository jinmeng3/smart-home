from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY, SETTINGS_DEPENDENCY
from app.core.config import Settings
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.device import (
    DeviceBatchGroup,
    DeviceBatchGroupResult,
    DeviceCreate,
    DeviceDetailRead,
    DeviceDetailWithLogs,
    DeviceImageRead,
    DeviceListRead,
    DeviceLogListRead,
    DeviceQueryParams,
    DeviceSync,
    DeviceSyncRead,
    DeviceUpdate,
)
from app.services.device import (
    add_device_service,
    batch_group_devices_service,
    delete_device_service,
    get_device_service,
    list_device_logs_service,
    list_devices_service,
    sync_devices_service,
    update_device_service,
    upload_image_service,
)

router = APIRouter(prefix="/devices", tags=["devices"])
# FastAPI 参数对象在模块加载时创建，避免在函数默认值中执行调用。
DEVICE_ID_QUERY = Query(default=None)
LOG_PAGE_QUERY = Query(default=1, ge=1)
LOG_PAGE_SIZE_QUERY = Query(default=20, ge=1, le=100)
UPLOAD_IMAGE_FILE = File(...)


# === 设备 CRUD ===


@router.get("", response_model=ApiResponse[DeviceListRead])
def list_devices(
    params: Annotated[DeviceQueryParams, Query()],
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceListRead]:
    """按关键字和设备属性筛选分页列表。"""
    return ApiResponse(data=list_devices_service(db, current_user, params))


@router.post(
    "",
    response_model=ApiResponse[DeviceDetailRead],
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/add",
    response_model=ApiResponse[DeviceDetailRead],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    deprecated=True,
)
def add_device(
    payload: DeviceCreate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceDetailRead]:
    """创建设备并写入创建日志。"""
    return ApiResponse(
        data=add_device_service(db, current_user, payload), message="created"
    )


@router.get("/{device_id}", response_model=ApiResponse[DeviceDetailWithLogs])
def get_device(
    device_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceDetailWithLogs]:
    """读取设备详情及最近操作日志。"""
    return ApiResponse(data=get_device_service(db, current_user, device_id))


@router.patch("/{device_id}", response_model=ApiResponse[DeviceDetailRead])
@router.put(
    "/{device_id}",
    response_model=ApiResponse[DeviceDetailRead],
    include_in_schema=False,
    deprecated=True,
)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceDetailRead]:
    """更新设备信息和在线状态。"""
    return ApiResponse(data=update_device_service(db, current_user, device_id, payload))


@router.delete("/{device_id}", response_model=ApiResponse[None])
def remove_device(
    device_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[None]:
    """删除设备及其关联日志。"""
    delete_device_service(db, current_user, device_id)
    return ApiResponse(message="deleted")


# === 设备同步 ===


@router.post("/sync", response_model=ApiResponse[DeviceSyncRead])
def sync_devices(
    payload: DeviceSync,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceSyncRead]:
    """同步指定接入平台下的设备。"""
    return ApiResponse(data=sync_devices_service(db, current_user, payload.platform))


# === 设备日志 ===


@router.get("/{device_id}/logs", response_model=ApiResponse[DeviceLogListRead])
def list_device_logs(
    device_id: int,
    page: int = LOG_PAGE_QUERY,
    page_size: int = LOG_PAGE_SIZE_QUERY,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceLogListRead]:
    """分页读取指定设备的操作日志。"""
    return ApiResponse(
        data=list_device_logs_service(db, current_user, device_id, page, page_size)
    )


# === 设备图片 ===


@router.post("/images", response_model=ApiResponse[DeviceImageRead])
def upload_image(
    file: UploadFile = UPLOAD_IMAGE_FILE,
    device_id: int | None = DEVICE_ID_QUERY,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceImageRead]:
    """上传设备图片，可选关联已有设备。"""
    return ApiResponse.ok(
        data=upload_image_service(db, current_user, device_id, file, settings),
        message="uploaded",
    )


# === 设备分组 ===


@router.post("/groups/assign", response_model=ApiResponse[DeviceBatchGroupResult])
def batch_assign_group(
    payload: DeviceBatchGroup,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[DeviceBatchGroupResult]:
    """创建或复用分组，并将指定设备批量分配。"""
    return ApiResponse(data=batch_group_devices_service(db, current_user, payload))
