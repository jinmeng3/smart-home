from datetime import date

from fastapi import APIRouter, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.room import (
    RoomDetailRead,
    RoomDeviceListRead,
    RoomDeviceMetaWrite,
    RoomDevicesWrite,
    RoomDeviceWrite,
    RoomEnvironmentLatestRead,
    RoomEnvironmentReportRead,
    RoomEnvironmentTrendRead,
    RoomInput,
    RoomListRead,
    RoomLogListRead,
    RoomQuickActionWrite,
    RoomRead,
    RoomSceneExecuteWrite,
    RoomStatsRead,
)
from app.schemas.scene import SceneExecutionRead, SceneListRead, ScenePreviewRead
from app.services.room import (
    add_room_service,
    create_room_environment_report_service,
    delete_room_service,
    edit_room_device_service,
    edit_room_service,
    execute_room_scene_service,
    get_room_detail_service,
    get_room_devices_service,
    get_room_environment_latest_service,
    get_room_environment_trends_service,
    get_room_logs_service,
    get_room_scenes_service,
    list_room_stats_service,
    list_rooms_service,
    preview_room_scene_service,
    quick_action_service,
    set_room_devices_service,
    update_device_service,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


# === 房间 CRUD ===


@router.get("", response_model=ApiResponse[RoomListRead])
def list_rooms(
    floor: str | None = Query(default=None),
    room_type: str | None = Query(default=None),
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomListRead]:
    """按楼层和类型筛选房间列表。"""
    return ApiResponse.ok(data=list_rooms_service(db, current_user, floor, room_type))


@router.get("/stats", response_model=ApiResponse[RoomStatsRead])
def list_room_stats(
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomStatsRead]:
    """获取房间统计概览"""
    return ApiResponse.ok(list_room_stats_service(db, current_user))


@router.get("/{room_id}", response_model=ApiResponse[RoomDetailRead])
@router.get(
    "/{room_id}/detail",
    response_model=ApiResponse[RoomDetailRead],
    include_in_schema=False,
    deprecated=True,
)
def get_room_detail(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDetailRead]:
    """获取房间详情"""
    return ApiResponse.ok(get_room_detail_service(db, current_user, room_id))


@router.post(
    "", response_model=ApiResponse[RoomRead], status_code=status.HTTP_201_CREATED
)
@router.post(
    "/add",
    response_model=ApiResponse[RoomRead],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    deprecated=True,
)
def add_room(
    payload: RoomInput,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    """创建房间。"""
    return ApiResponse.ok(add_room_service(db, current_user, payload), "created")


@router.patch("/{room_id}", response_model=ApiResponse[RoomRead])
@router.put(
    "/{room_id}",
    response_model=ApiResponse[RoomRead],
    include_in_schema=False,
    deprecated=True,
)
def edit_room(
    room_id: int,
    payload: RoomInput,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    """更新房间信息。"""
    return ApiResponse.ok(edit_room_service(db, current_user, room_id, payload))


@router.delete("/{room_id}", response_model=ApiResponse[None])
def delete_room(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[None]:
    """删除房间。"""
    delete_room_service(db, current_user, room_id)
    return ApiResponse.ok(message="deleted")


# === 房间日志 ===


@router.get("/{room_id}/logs", response_model=ApiResponse[RoomLogListRead])
def get_room_logs(
    room_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomLogListRead]:
    """分页查询房间操作日志，支持日期范围和关键字筛选。"""
    return ApiResponse.ok(
        get_room_logs_service(
            db, current_user, room_id, page, page_size, keyword, date_from, date_to
        )
    )


# === 房间设备 ===


@router.get("/{room_id}/devices", response_model=ApiResponse[RoomDeviceListRead])
def get_room_devices(
    room_id: int,
    keyword: str | None = None,
    type: str | None = None,
    status: str | None = None,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    """查询房间内设备，支持关键字、类型和状态筛选。"""
    return ApiResponse.ok(
        get_room_devices_service(db, current_user, room_id, keyword, type, status)
    )


@router.put("/{room_id}/devices", response_model=ApiResponse[RoomDeviceListRead])
def set_room_devices(
    room_id: int,
    payload: RoomDevicesWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    """整体替换房间的设备绑定关系。"""
    return ApiResponse.ok(set_room_devices_service(db, current_user, room_id, payload))


@router.patch(
    "/{room_id}/devices/{device_id}", response_model=ApiResponse[RoomDeviceListRead]
)
def edit_room_device(
    room_id: int,
    device_id: int,
    payload: RoomDeviceMetaWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    """修改房间内设备的绑定元信息（分组、收藏、排序等）。"""
    return ApiResponse.ok(
        edit_room_device_service(db, current_user, room_id, device_id, payload)
    )


@router.patch("/{room_id}/device", response_model=ApiResponse[RoomRead])
def update_device(
    room_id: int,
    payload: RoomDeviceWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    """更新房间内设备的实时状态值。"""
    return ApiResponse.ok(
        update_device_service(db, current_user, room_id, payload), "设备状态已更新"
    )


@router.post("/{room_id}/quick-action", response_model=ApiResponse[RoomRead])
def quick_action(
    room_id: int,
    payload: RoomQuickActionWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    """执行房间快捷操作（如全开灯、空调、窗帘）。"""
    return ApiResponse.ok(
        quick_action_service(db, current_user, room_id, payload), "快捷操作已执行"
    )



# === 房间场景 ===


@router.get("/{room_id}/scenes", response_model=ApiResponse[SceneListRead])
def get_room_scenes(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneListRead]:
    """查询房间关联的场景。"""
    return ApiResponse.ok(get_room_scenes_service(db, current_user, room_id))


@router.post(
    "/{room_id}/scenes/{scene_id}/preview", response_model=ApiResponse[ScenePreviewRead]
)
def preview_room_scene(
    room_id: int,
    scene_id: str,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScenePreviewRead]:
    """预览房间场景动作链，不实际执行。"""
    return ApiResponse.ok(
        preview_room_scene_service(db, current_user, room_id, scene_id)
    )


@router.post(
    "/{room_id}/scenes/{scene_id}/execute",
    response_model=ApiResponse[SceneExecutionRead],
)
def execute_room_scene(
    room_id: int,
    scene_id: str,
    payload: RoomSceneExecuteWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneExecutionRead]:
    """执行房间场景并记录活动日志。"""
    return ApiResponse.ok(
        execute_room_scene_service(db, current_user, room_id, scene_id, payload)
    )


# === 房间环境 ===


@router.get(
    "/{room_id}/environment/latest",
    response_model=ApiResponse[RoomEnvironmentLatestRead],
)
def get_room_environment_latest(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomEnvironmentLatestRead]:
    """获取房间最新环境数据（温度、湿度等）。"""
    return ApiResponse.ok(
        get_room_environment_latest_service(db, current_user, room_id)
    )


@router.get(
    "/{room_id}/environment/trends",
    response_model=ApiResponse[RoomEnvironmentTrendRead],
)
def get_room_environment_trends(
    room_id: int,
    metrics: str = Query(default="temperature,humidity"),
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomEnvironmentTrendRead]:
    """获取房间环境趋势数据。"""
    return ApiResponse.ok(
        get_room_environment_trends_service(db, current_user, room_id, metrics)
    )


@router.post(
    "/{room_id}/environment/reports",
    response_model=ApiResponse[RoomEnvironmentReportRead],
    status_code=status.HTTP_201_CREATED,
)
def create_room_environment_report(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomEnvironmentReportRead]:
    """创建房间环境报告任务。"""
    return ApiResponse.ok(
        create_room_environment_report_service(db, current_user, room_id),
        message="created",
    )
