import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    CURRENT_USER_DEPENDENCY,
    DB_DEPENDENCY,
    HOUSEHOLD_MEMBER_DEPENDENCY,
)
from app.models.automation import Automation
from app.models.device import Device
from app.models.overview import (
    DeviceSyncJob,
    HouseholdSchedule,
    InspectionJob,
    OverviewExecution,
)
from app.models.room import Room, RoomDevice
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.device import DeviceListRead, DeviceRead
from app.schemas.overview import (
    HomeStatus,
    InspectionWrite,
    ModeExecuteWrite,
    OverviewRead,
    OverviewRoom,
    OverviewSummary,
    ScheduleRead,
    ScheduleWrite,
    SyncJobRead,
    SyncJobWrite,
    TaskRead,
)
from app.services.household import get_default_household_id

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
    rooms = list(
        db.scalars(
            select(Room).where(Room.household_id == household_id).order_by(Room.id)
        ).all()
    )
    device_rows = (
        db.execute(
                select(RoomDevice.room_id, Device)
                .join(RoomDevice, RoomDevice.device_id == Device.id)
                .where(RoomDevice.room_id.in_([room.id for room in rooms]))
                .order_by(Device.updated_at.desc())
            ).all()
        if rooms
        else []
    )
    devices_by_room: dict[int, list[Device]] = {}
    devices: list[Device] = []
    seen_device_ids: set[int] = set()
    for room_id, device in device_rows:
        devices_by_room.setdefault(room_id, []).append(device)
        if device.id not in seen_device_ids:
            seen_device_ids.add(device.id)
            devices.append(device)
    online = sum(item.status in {"online", "running"} for item in devices)
    running = (
        db.scalar(
            select(func.count())
            .select_from(Automation)
            .where(
                Automation.household_id == household_id, Automation.enabled.is_(True)
            )
        )
        or 0
    )
    room_items = []
    for room in rooms:
        room_devices = devices_by_room.get(room.id, [])
        lights = [item for item in room_devices if item.type == "light"]
        room_items.append(
            OverviewRoom(
                id=room.id,
                name=room.name,
                device_count=len(room_devices),
                light_on=sum(item.status in {"online", "running"} for item in lights),
                light_total=len(lights),
                temperature=0,
                device_summaries=[
                    f"{item.name} {item.status}" for item in room_devices[:2]
                ],
            )
        )
    recent = [
        {
            "id": item.id,
            "name": item.name,
            "room_name": item.room,
            "online": item.status in {"online", "running"},
            "state_text": item.status,
            "updated_at": item.updated_at,
        }
        for item in devices[:10]
    ]
    return ApiResponse.ok(
        OverviewRead(
            summary=OverviewSummary(
                device_total=len(devices),
                device_online=online,
                running_automation_count=running,
            ),
            home_status=HomeStatus(
                people_home=0,
                temperature=0,
                humidity=0,
                air_quality="excellent",
                pm25=0,
            ),
            rooms=room_items,
            recent_devices=recent,
        )
    )


@router.get(
    "/households/{household_id}/devices", response_model=ApiResponse[DeviceListRead]
)
def get_household_devices(
    household_id: int,
    _membership=HOUSEHOLD_MEMBER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[DeviceListRead]:
    """列出家庭下全部房间关联的设备。"""
    devices = list(
        db.scalars(
            select(Device)
            .join(RoomDevice, RoomDevice.device_id == Device.id)
            .join(Room, Room.id == RoomDevice.room_id)
            .where(Room.household_id == household_id)
            .order_by(Device.updated_at.desc())
        ).all()
    )
    return ApiResponse.ok(
        DeviceListRead(
            total=len(devices),
            page=1,
            page_size=max(1, len(devices)),
            items=[DeviceRead.model_validate(item) for item in devices],
        )
    )


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
    key = f"household-{household_id}-{datetime.now(timezone.utc).date().isoformat()}"
    job = db.scalar(
        select(DeviceSyncJob).where(
            DeviceSyncJob.household_id == household_id,
            DeviceSyncJob.idempotency_key == key,
        )
    )
    if not job:
        job = DeviceSyncJob(
            household_id=household_id,
            scope="all",
            sources_json="[]",
            options_json="{}",
            idempotency_key=key,
            created_by=user.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    return ApiResponse.ok(
        SyncJobRead(
            id=job.id, status=job.status, statistics=json.loads(job.statistics_json)
        )
    )


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
    household_id = get_default_household_id(db, user)
    existing = db.scalar(
        select(OverviewExecution).where(
            OverviewExecution.household_id == household_id,
            OverviewExecution.idempotency_key == payload.idempotency_key,
        )
    )
    if existing:
        return ApiResponse.ok(
            TaskRead(
                id=existing.id,
                status=existing.status,
                affected_device_count=existing.affected_device_count,
            )
        )
    room_query = select(Room).where(Room.household_id == household_id)
    if payload.room_ids:
        room_query = room_query.where(Room.id.in_(payload.room_ids))
    rooms = list(db.scalars(room_query).all())
    if payload.room_ids and len(rooms) != len(set(payload.room_ids)):
        raise HTTPException(status_code=422, detail="部分房间不存在或不属于当前家庭")
    affected = (
        db.scalar(
            select(func.count())
            .select_from(Device)
            .join(RoomDevice, RoomDevice.device_id == Device.id)
            .where(RoomDevice.room_id.in_([item.id for item in rooms]))
        )
        or 0
    )
    task = OverviewExecution(
        household_id=household_id,
        mode=payload.mode,
        room_ids_json=json.dumps(payload.room_ids),
        status="queued",
        affected_device_count=affected,
        requested_by=user.id,
        idempotency_key=payload.idempotency_key,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ApiResponse.ok(
        TaskRead(id=task.id, status=task.status, affected_device_count=affected)
    )


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
    household_id = get_default_household_id(db, user)
    count = (
        db.scalar(
            select(func.count())
            .select_from(Device)
            .join(RoomDevice, RoomDevice.device_id == Device.id)
            .join(Room, Room.id == RoomDevice.room_id)
            .where(Room.household_id == household_id)
        )
        or 0
    )
    job = InspectionJob(
        household_id=household_id,
        scope=payload.scope,
        room_ids_json=json.dumps(payload.room_ids),
        checks_json=json.dumps(payload.checks),
        device_count=count,
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return ApiResponse.ok(
        TaskRead(
            id=job.id,
            status=job.status,
            device_count=count,
            checked_count=0,
            estimated_seconds=max(2, count),
        )
    )


@router.get("/inspections/{inspection_id}", response_model=ApiResponse[TaskRead])
def get_inspection(
    inspection_id: int,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[TaskRead]:
    """查询巡检任务的执行进度。"""
    job = db.scalar(
        select(InspectionJob).where(
            InspectionJob.id == inspection_id,
            InspectionJob.household_id == get_default_household_id(db, user),
        )
    )
    if not job:
        raise HTTPException(status_code=404, detail="巡检任务不存在")
    return ApiResponse.ok(
        TaskRead(
            id=job.id,
            status=job.status,
            device_count=job.device_count,
            checked_count=job.checked_count,
        )
    )


# === 家庭日程 ===


@router.put("/schedules/{schedule_date}", response_model=ApiResponse[ScheduleRead])
def save_schedule(
    schedule_date: date,
    payload: ScheduleWrite,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScheduleRead]:
    """保存或更新家庭某天的日程安排，带版本冲突校验。"""
    household_id = get_default_household_id(db, user)
    schedule = db.scalar(
        select(HouseholdSchedule).where(
            HouseholdSchedule.household_id == household_id,
            HouseholdSchedule.schedule_date == schedule_date,
        )
    )
    if schedule and payload.version is not None and schedule.version != payload.version:
        raise HTTPException(
            status_code=409,
            detail={"message": "日程版本冲突", "version": schedule.version},
        )
    if not schedule:
        schedule = HouseholdSchedule(
            household_id=household_id, schedule_date=schedule_date
        )
        db.add(schedule)
    else:
        schedule.version += 1
    schedule.enabled = payload.enabled
    schedule.repeat_days_json = json.dumps(payload.repeat_days)
    schedule.targets_json = json.dumps(payload.targets)
    schedule.items_json = json.dumps(payload.items, ensure_ascii=False)
    db.commit()
    db.refresh(schedule)
    return ApiResponse.ok(
        ScheduleRead(
            id=schedule.id,
            schedule_date=schedule.schedule_date,
            enabled=schedule.enabled,
            repeat_days=json.loads(schedule.repeat_days_json),
            targets=json.loads(schedule.targets_json),
            items=json.loads(schedule.items_json),
            version=schedule.version,
            updated_at=schedule.updated_at,
        )
    )


@router.get(
    "/schedules/{schedule_date}", response_model=ApiResponse[ScheduleRead | None]
)
def read_schedule(
    schedule_date: date,
    db: Session = DB_DEPENDENCY,
    user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScheduleRead | None]:
    """读取家庭某天的日程安排，未设置时返回null。"""
    household_id = get_default_household_id(db, user)
    schedule = db.scalar(
        select(HouseholdSchedule).where(
            HouseholdSchedule.household_id == household_id,
            HouseholdSchedule.schedule_date == schedule_date,
        )
    )
    if not schedule:
        return ApiResponse.ok(None)
    return ApiResponse.ok(
        ScheduleRead(
            id=schedule.id,
            schedule_date=schedule.schedule_date,
            enabled=schedule.enabled,
            repeat_days=json.loads(schedule.repeat_days_json),
            targets=json.loads(schedule.targets_json),
            items=json.loads(schedule.items_json),
            version=schedule.version,
            updated_at=schedule.updated_at,
        )
    )


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
    household_id = get_default_household_id(db, user)
    job = db.scalar(
        select(DeviceSyncJob).where(
            DeviceSyncJob.household_id == household_id,
            DeviceSyncJob.idempotency_key == payload.idempotency_key,
        )
    )
    if not job:
        job = DeviceSyncJob(
            household_id=household_id,
            scope=payload.scope,
            sources_json=json.dumps(payload.sources),
            options_json=json.dumps(payload.options),
            idempotency_key=payload.idempotency_key,
            created_by=user.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    return ApiResponse.ok(
        SyncJobRead(
            id=job.id, status=job.status, statistics=json.loads(job.statistics_json)
        )
    )


@router.get("/device-sync-jobs/{job_id}", response_model=ApiResponse[SyncJobRead])
def get_sync_job(
    job_id: int, db: Session = DB_DEPENDENCY, user: User = CURRENT_USER_DEPENDENCY
) -> ApiResponse[SyncJobRead]:
    """查询设备同步任务的状态与统计。"""
    job = db.scalar(
        select(DeviceSyncJob).where(
            DeviceSyncJob.id == job_id,
            DeviceSyncJob.household_id == get_default_household_id(db, user),
        )
    )
    if not job:
        raise HTTPException(status_code=404, detail="同步任务不存在")
    return ApiResponse.ok(
        SyncJobRead(
            id=job.id, status=job.status, statistics=json.loads(job.statistics_json)
        )
    )
