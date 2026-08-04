import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.automation import (
    Automation,
    AutomationAction,
    AutomationCondition,
    AutomationExecution,
    AutomationTrigger,
)
from app.models.device import Device
from app.models.room import Room
from app.schemas.automation import (
    ActionWrite,
    AutomationCreate,
    AutomationListItem,
    AutomationListRead,
    AutomationRead,
    AutomationSummary,
    AutomationUpdate,
    BatchEnableRead,
    BatchEnableWrite,
    ConditionWrite,
    ExecuteRead,
    ExecutionListRead,
    ExecutionRead,
    FlowItem,
)


def automation_query():
    return select(Automation).options(
        selectinload(Automation.triggers),
        selectinload(Automation.conditions),
        selectinload(Automation.actions),
    )


def get_automation(
    db: Session, automation_id: int, household_id: int | None = None
) -> Automation:
    query = automation_query().where(Automation.id == automation_id)
    if household_id is not None:
        query = query.where(Automation.household_id == household_id)
    automation = db.scalar(query)
    if not automation:
        raise HTTPException(status_code=404, detail="自动化规则不存在")
    return automation


def serialize(automation: Automation) -> AutomationRead:
    triggers = [
        FlowItem(type=item.type, config=json.loads(item.config_json))
        for item in automation.triggers
    ]
    conditions = [
        ConditionWrite(
            type=item.type, config=json.loads(item.config_json), position=item.position
        )
        for item in sorted(automation.conditions, key=lambda item: item.position)
    ]
    actions = [
        ActionWrite(
            type=item.type,
            config=json.loads(item.config_json),
            position=item.position,
            device_id=item.device_id,
            scene_id=item.scene_id,
        )
        for item in sorted(automation.actions, key=lambda item: item.position)
    ]
    return AutomationRead(
        id=automation.id,
        household_id=automation.household_id,
        name=automation.name,
        description=automation.description,
        trigger_type=automation.trigger_type,
        enabled=automation.enabled,
        device_count=len({item.device_id for item in actions if item.device_id}),
        priority=automation.priority,
        cooldown_seconds=automation.cooldown_seconds,
        delay_seconds=automation.delay_seconds,
        note=automation.note,
        version=automation.version,
        triggers=triggers,
        conditions=conditions,
        actions=actions,
        created_at=automation.created_at,
        updated_at=automation.updated_at,
    )


def validate_devices(
    db: Session, household_id: int, actions: list[ActionWrite]
) -> None:
    device_ids = {item.device_id for item in actions if item.device_id is not None}
    if not device_ids:
        return
    room_names = select(Room.name).where(Room.household_id == household_id)
    found = set(
        db.scalars(
            select(Device.id).where(
                Device.id.in_(device_ids), Device.room.in_(room_names)
            )
        ).all()
    )
    if found != device_ids:
        raise HTTPException(status_code=422, detail="动作设备不属于当前家庭或不存在")


def replace_flow(
    automation: Automation, payload: AutomationCreate | AutomationUpdate
) -> None:
    if payload.triggers is not None:
        automation.triggers = [
            AutomationTrigger(
                type=item.type, config_json=json.dumps(item.config, ensure_ascii=False)
            )
            for item in payload.triggers
        ]
        automation.trigger_type = (
            payload.triggers[0].type if payload.triggers else "manual"
        )
    if payload.conditions is not None:
        automation.conditions = [
            AutomationCondition(
                type=item.type,
                config_json=json.dumps(item.config, ensure_ascii=False),
                position=item.position if item.position is not None else index,
            )
            for index, item in enumerate(payload.conditions)
        ]
    if payload.actions is not None:
        automation.actions = [
            AutomationAction(
                type=item.type,
                device_id=item.device_id,
                scene_id=item.scene_id,
                config_json=json.dumps(item.config, ensure_ascii=False),
                position=item.position,
            )
            for item in payload.actions
        ]


def create_automation(
    db: Session, household_id: int, user_id: int, payload: AutomationCreate
) -> AutomationRead:
    validate_devices(db, household_id, payload.actions)
    if db.scalar(
        select(Automation.id).where(
            Automation.household_id == household_id,
            Automation.name == payload.name.strip(),
        )
    ):
        raise HTTPException(status_code=409, detail="自动化名称已存在")
    automation = Automation(household_id=household_id, created_by=user_id)
    for field in (
        "name",
        "description",
        "enabled",
        "priority",
        "cooldown_seconds",
        "delay_seconds",
        "note",
    ):
        setattr(automation, field, getattr(payload, field))
    replace_flow(automation, payload)
    db.add(automation)
    db.commit()
    return serialize(get_automation(db, automation.id))


def update_automation(
    db: Session, automation_id: int, household_id: int, payload: AutomationUpdate
) -> AutomationRead:
    automation = get_automation(db, automation_id, household_id)
    if payload.version is not None and payload.version != automation.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="自动化规则版本冲突"
        )
    if payload.actions is not None:
        validate_devices(db, household_id, payload.actions)
        positions = [item.position for item in payload.actions]
        if len(positions) != len(set(positions)):
            raise HTTPException(status_code=422, detail="动作 position 不能重复")
    for field in (
        "name",
        "description",
        "enabled",
        "priority",
        "cooldown_seconds",
        "delay_seconds",
        "note",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(automation, field, value)
    replace_flow(automation, payload)
    automation.version += 1
    db.commit()
    return serialize(get_automation(db, automation.id))


def list_automations(
    db: Session,
    household_id: int,
    keyword: str | None,
    trigger_type: str | None,
    enabled: bool | None,
    page: int,
    page_size: int,
) -> AutomationListRead:
    filters = [Automation.household_id == household_id]
    if keyword:
        term = f"%{keyword.strip()}%"
        filters.append(
            or_(Automation.name.like(term), Automation.description.like(term))
        )
    if trigger_type:
        filters.append(Automation.trigger_type == trigger_type)
    if enabled is not None:
        filters.append(Automation.enabled.is_(enabled))
    total = db.scalar(select(func.count()).select_from(Automation).where(*filters)) or 0
    rows = db.scalars(
        automation_query()
        .where(*filters)
        .order_by(Automation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    enabled_count = (
        db.scalar(
            select(func.count())
            .select_from(Automation)
            .where(
                Automation.household_id == household_id, Automation.enabled.is_(True)
            )
        )
        or 0
    )
    execution_base = (
        select(func.count())
        .select_from(AutomationExecution)
        .join(Automation)
        .where(Automation.household_id == household_id)
    )
    running = (
        db.scalar(
            execution_base.where(AutomationExecution.status.in_(["queued", "running"]))
        )
        or 0
    )
    executions_today = (
        db.scalar(execution_base.where(AutomationExecution.started_at >= today)) or 0
    )
    abnormal = (
        db.scalar(
            execution_base.where(
                AutomationExecution.status == "failed",
                AutomationExecution.started_at >= today,
            )
        )
        or 0
    )
    items = [
        AutomationListItem(
            id=row.id,
            name=row.name,
            description=row.description,
            trigger_type=row.trigger_type,
            enabled=row.enabled,
            device_count=len(
                {item.device_id for item in row.actions if item.device_id}
            ),
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return AutomationListRead(
        summary=AutomationSummary(
            enabled=enabled_count,
            total=db.scalar(
                select(func.count())
                .select_from(Automation)
                .where(Automation.household_id == household_id)
            )
            or 0,
            running=running,
            executions_today=executions_today,
            abnormal=abnormal,
        ),
        items=items,
        total=total,
    )


def execute_automation(
    db: Session, automation: Automation, source: str, idempotency_key: str | None
) -> ExecuteRead:
    if idempotency_key:
        existing = db.scalar(
            select(AutomationExecution).where(
                AutomationExecution.idempotency_key == idempotency_key
            )
        )
        if existing:
            return ExecuteRead(execution_id=existing.id, status=existing.status)
    if not automation.enabled:
        raise HTTPException(status_code=409, detail="自动化规则已停用")
    execution = AutomationExecution(
        automation_id=automation.id,
        source=source,
        status="running",
        idempotency_key=idempotency_key,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return ExecuteRead(execution_id=execution.id, status=execution.status)


def list_executions(
    db: Session,
    automation: Automation,
    page: int,
    page_size: int,
    execution_status: str | None,
) -> ExecutionListRead:
    filters = [AutomationExecution.automation_id == automation.id]
    if execution_status:
        filters.append(AutomationExecution.status == execution_status)
    total = (
        db.scalar(select(func.count()).select_from(AutomationExecution).where(*filters))
        or 0
    )
    rows = db.scalars(
        select(AutomationExecution)
        .where(*filters)
        .order_by(AutomationExecution.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ExecutionListRead(
        total=total,
        items=[
            ExecutionRead(
                id=item.id,
                status=item.status,
                source=item.source,
                trigger_snapshot=json.loads(item.trigger_snapshot),
                duration_ms=item.duration_ms,
                error_message=item.error_message,
                started_at=item.started_at,
                finished_at=item.finished_at,
            )
            for item in rows
        ],
    )


def batch_enable(
    db: Session, household_id: int, payload: BatchEnableWrite
) -> BatchEnableRead:
    rows = list(
        db.scalars(
            select(Automation).where(
                Automation.household_id == household_id,
                Automation.id.in_(payload.rule_ids),
            )
        ).all()
    )
    if len(rows) != len(set(payload.rule_ids)):
        raise HTTPException(
            status_code=422, detail="部分自动化规则不存在或不属于当前家庭"
        )
    unchanged = sum(item.enabled for item in rows)
    for item in rows:
        item.enabled = True
        item.version += 1
    db.commit()
    return BatchEnableRead(
        updated_count=len(rows) - unchanged, unchanged_count=unchanged
    )
