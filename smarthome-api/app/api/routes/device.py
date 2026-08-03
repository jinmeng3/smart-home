from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import DB_DEPENDENCY, SETTINGS_DEPENDENCY
from app.core.config import Settings
from app.schemas.common import ApiResponse
from app.schemas.device import (
    DeviceCreate,
    DeviceDetailRead,
    DeviceDetailWithLogs,
    DeviceListRead,
    DeviceLogListRead,
    DeviceQueryParams,
    DeviceSync,
    DeviceSyncRead,
    DeviceUpdate,
)
from app.services.device import (
    create_device,
    delete_device,
    list_device_logs,
    list_devices,
    read_device,
    sync_devices,
    update_device,
    upload_device_image,
)

router = APIRouter(prefix="/devices", tags=["devices"])
# FastAPI 参数对象在模块加载时创建，避免在函数默认值中执行调用。
DEVICE_ID_QUERY = Query(default=None)
LOG_PAGE_QUERY = Query(default=1, ge=1)
LOG_PAGE_SIZE_QUERY = Query(default=20, ge=1, le=100)
UPLOAD_IMAGE_FILE = File(...)


@router.get("", response_model=ApiResponse[DeviceListRead])
def get_devices(
    params: Annotated[DeviceQueryParams, Query()],
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceListRead]:
    """按关键字和设备属性筛选分页列表。"""
    return ApiResponse(data=list_devices(db, params))


@router.post(
    "",
    response_model=ApiResponse[DeviceDetailRead],
    status_code=status.HTTP_201_CREATED,
)
def add_device(
    payload: DeviceCreate, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceDetailRead]:
    """创建设备并写入创建日志。"""
    return ApiResponse(data=create_device(db, payload), message="created")


@router.post("/sync", response_model=ApiResponse[DeviceSyncRead])
def synchronize_devices(
    payload: DeviceSync, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceSyncRead]:
    """同步指定接入平台下的设备。"""
    return ApiResponse(data=sync_devices(db, payload.platform))


@router.get("/{device_id}", response_model=ApiResponse[DeviceDetailWithLogs])
def get_device(
    device_id: int, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceDetailWithLogs]:
    """读取设备详情及最近操作日志。"""
    return ApiResponse(data=read_device(db, device_id))


@router.put("/{device_id}", response_model=ApiResponse[DeviceDetailRead])
def edit_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceDetailRead]:
    """更新设备信息和在线状态。"""
    return ApiResponse(data=update_device(db, device_id, payload))


@router.delete("/{device_id}", response_model=ApiResponse[None])
def remove_device(device_id: int, db: Session = DB_DEPENDENCY) -> ApiResponse[None]:
    """删除设备及其关联日志。"""
    delete_device(db, device_id)
    return ApiResponse(message="deleted")


@router.get("/{device_id}/logs", response_model=ApiResponse[DeviceLogListRead])
def get_device_logs(
    device_id: int,
    page: int = LOG_PAGE_QUERY,
    page_size: int = LOG_PAGE_SIZE_QUERY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceLogListRead]:
    """分页读取指定设备的操作日志。"""
    return ApiResponse(data=list_device_logs(db, device_id, page, page_size))


@router.post("/images", response_model=ApiResponse[str])
def upload_image(
    file: UploadFile = UPLOAD_IMAGE_FILE,
    device_id: int | None = DEVICE_ID_QUERY,
    db: Session = DB_DEPENDENCY,
    settings: Settings = SETTINGS_DEPENDENCY,
) -> ApiResponse[str]:
    """上传设备图片，可选关联已有设备。"""
    return ApiResponse.ok(data=upload_device_image(db, device_id, file, settings))
