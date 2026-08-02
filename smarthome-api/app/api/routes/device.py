from fastapi import APIRouter, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DB_DEPENDENCY
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
)

router = APIRouter(prefix="/devices", tags=["devices"])
DEVICE_QUERY_PARAMS = Query()
LOG_PAGE_QUERY = Query(default=1, ge=1)
LOG_PAGE_SIZE_QUERY = Query(default=20, ge=1, le=100)


@router.get("", response_model=ApiResponse[DeviceListRead])
def get_devices(
    params: DeviceQueryParams = DEVICE_QUERY_PARAMS,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceListRead]:
    return ApiResponse(data=list_devices(db, params))


@router.post(
    "",
    response_model=ApiResponse[DeviceDetailRead],
    status_code=status.HTTP_201_CREATED,
)
def add_device(
    payload: DeviceCreate, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceDetailRead]:
    return ApiResponse(data=create_device(db, payload), message="created")


@router.post("/sync", response_model=ApiResponse[DeviceSyncRead])
def synchronize_devices(
    payload: DeviceSync, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceSyncRead]:
    return ApiResponse(data=sync_devices(db, payload.platform))


@router.get("/{device_id}", response_model=ApiResponse[DeviceDetailWithLogs])
def get_device(
    device_id: int, db: Session = DB_DEPENDENCY
) -> ApiResponse[DeviceDetailWithLogs]:
    return ApiResponse(data=read_device(db, device_id))


@router.put("/{device_id}", response_model=ApiResponse[DeviceDetailRead])
def edit_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceDetailRead]:
    return ApiResponse(data=update_device(db, device_id, payload))


@router.delete("/{device_id}", response_model=ApiResponse[None])
def remove_device(device_id: int, db: Session = DB_DEPENDENCY) -> ApiResponse[None]:
    delete_device(db, device_id)
    return ApiResponse(message="deleted")


@router.get("/{device_id}/logs", response_model=ApiResponse[DeviceLogListRead])
def get_device_logs(
    device_id: int,
    page: int = LOG_PAGE_QUERY,
    page_size: int = LOG_PAGE_SIZE_QUERY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceLogListRead]:
    return ApiResponse(data=list_device_logs(db, device_id, page, page_size))
