from datetime import date

from fastapi import APIRouter, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.device import DeviceListRead, TodayEnergyRead
from app.schemas.overview import (
    InspectionWrite,
    ModeExecuteWrite,
    OverviewRead,
    ScheduleRead,
    ScheduleWrite,
    SyncJobRead,
    SyncJobWrite,
    TaskRead,
)
from app.schemas.room import RoomEnvironmentReportRead
from app.services.device import get_today_energy_service
from app.services.overview import (
    create_inspection_service,
    create_sync_job_service,
    execute_mode_service,
    get_inspection_service,
    get_overview_service,
    get_sync_job_service,
    list_household_devices_service,
    read_schedule_service,
    save_schedule_service,
    sync_household_devices_service,
)
from app.services.room import get_environment_report_service

router = APIRouter(tags=["overview"])


# === 家庭概览 ===


@router.get(
    "/households/{household_id}/overview", response_model=ApiResponse[OverviewRead]
)
def get_overview(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[OverviewRead]:
    """聚合家庭概览数据：设备、自动化、环境与最近动态。"""
    return ApiResponse.ok(get_overview_service(db, household_id))


@router.get(
    "/households/{household_id}/devices", response_model=ApiResponse[DeviceListRead]
)
def get_household_devices(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceListRead]:
    """列出家庭下全部房间关联的设备。"""
    return ApiResponse.ok(list_household_devices_service(db, household_id))


@router.post(
    "/households/{household_id}/devices/sync",
    response_model=ApiResponse[SyncJobRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_household_devices(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SyncJobRead]:
    """按幂等键创建当天的设备同步任务。"""
    return ApiResponse.ok(sync_household_devices_service(db, household_id, user))


# === 模式与巡检 ===


@router.post(
    "/overview/modes/execute",
    response_model=ApiResponse[TaskRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def execute_mode(
    payload: ModeExecuteWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[TaskRead]:
    """按模式批量执行房间设备操作，支持幂等键去重。"""
    return ApiResponse.ok(execute_mode_service(db, user, payload))


@router.post(
    "/inspections",
    response_model=ApiResponse[TaskRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def create_inspection(
    payload: InspectionWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[TaskRead]:
    """创建设备巡检任务，记录检查范围并返回预估信息。"""
    return ApiResponse.ok(create_inspection_service(db, user, payload))


@router.get("/inspections/{inspection_id}", response_model=ApiResponse[TaskRead])
def get_inspection(
    inspection_id: int,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[TaskRead]:
    """查询巡检任务的执行进度。"""
    return ApiResponse.ok(get_inspection_service(db, user, inspection_id))


# === 家庭日程 ===


@router.put("/schedules/{schedule_date}", response_model=ApiResponse[ScheduleRead])
def save_schedule(
    schedule_date: date,
    payload: ScheduleWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScheduleRead]:
    """保存或更新家庭某天的日程安排，带版本冲突校验。"""
    return ApiResponse.ok(save_schedule_service(db, user, schedule_date, payload))


@router.get(
    "/schedules/{schedule_date}", response_model=ApiResponse[ScheduleRead | None]
)
def read_schedule(
    schedule_date: date,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScheduleRead | None]:
    """读取家庭某天的日程安排，未设置时返回null。"""
    return ApiResponse.ok(read_schedule_service(db, user, schedule_date))


# === 设备同步任务 ===


@router.post(
    "/device-sync-jobs",
    response_model=ApiResponse[SyncJobRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def create_sync_job(
    payload: SyncJobWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SyncJobRead]:
    """按幂等键创建设备同步任务。"""
    return ApiResponse.ok(create_sync_job_service(db, user, payload))


@router.get("/device-sync-jobs/{job_id}", response_model=ApiResponse[SyncJobRead])
def get_sync_job(
    job_id: int, db: Session = DB_DEPENDENCY, user: User = CURRENT_USER_DEPENDENCY
) -> ApiResponse[SyncJobRead]:
    """查询设备同步任务的状态与统计。"""
    return ApiResponse.ok(get_sync_job_service(db, user, job_id))


# === 环境报告 ===


@router.get(
    "/environment/reports/{task_id}",
    response_model=ApiResponse[RoomEnvironmentReportRead],
)
def get_environment_report(
    task_id: str,
) -> ApiResponse[RoomEnvironmentReportRead]:
    """查询环境报告任务状态。"""
    return ApiResponse.ok(get_environment_report_service(task_id))


@router.get(
    "/households/{household_id}/energy/today",
    response_model=ApiResponse[TodayEnergyRead],
)
def get_today_energy(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[TodayEnergyRead]:
    """查询指定家庭今日设备能耗汇总。"""
    return ApiResponse.ok(get_today_energy_service(db, current_user, household_id))
