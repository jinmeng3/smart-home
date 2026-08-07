import json
import re
from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import CursorResult, case, delete, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.device import Device
from app.models.room import Room
from app.models.scene import (
    Scene,
    SceneDraft,
    SceneExecutionLog,
    SceneExecutionStep,
    SceneRoom,
    SceneStep,
    SceneTemplate,
)
from app.schemas.scene import (
    SceneBatchEnabledResult,
    SceneBatchEnabledWrite,
    SceneBatchScheduleResult,
    SceneBatchScheduleWrite,
    SceneDraftRead,
    SceneDraftWrite,
    SceneExecutionRead,
    SceneExecutionStepRead,
    SceneListRead,
    SceneLogListRead,
    SceneLogRead,
    SceneOrderRead,
    SceneOrderWrite,
    ScenePreviewRead,
    ScenePreviewStep,
    SceneRead,
    SceneSummaryRead,
    SceneTemplateListRead,
    SceneTemplatePreviewRead,
    SceneTemplatePreviewStep,
    SceneTemplateRead,
    SceneTemplateUseWrite,
    SceneWrite,
    TriggerType,
)

HIGH_RISK_KEYWORDS = ("lock", "camera", "门锁", "摄像头", "安防")


# === 场景管理 ===


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_scene_or_404(db: Session, household_id: int, scene_id: str) -> Scene:
    scene = db.scalar(
        select(Scene)
        .options(selectinload(Scene.steps))
        .where(Scene.household_id == household_id, Scene.id == scene_id)
    )
    if not scene:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    return scene


def get_template_or_404(db: Session, template_id: str) -> SceneTemplate:
    template = db.get(SceneTemplate, template_id)
    if not template or not template.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在"
        )
    return template


def parse_json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def serialize_scene(scene: Scene) -> SceneRead:
    return SceneRead(
        id=scene.id,
        name=scene.name,
        description=scene.description,
        icon=scene.icon,
        color=scene.color,
        trigger_type=cast(TriggerType, scene.trigger_type),
        trigger_label=scene.trigger_label,
        room_labels=parse_json_list(scene.room_names),
        device_count=scene.device_count,
        enabled=scene.enabled,
        recommended=scene.recommended,
        high_risk=scene.high_risk,
        sort_order=scene.sort_order,
        source_template_id=scene.source_template_id,
        created_at=scene.created_at,
        updated_at=scene.updated_at,
        steps=[
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "device_id": step.device_id,
                "order": step.step_order,
            }
            for step in sorted(scene.steps, key=lambda item: item.step_order)
        ],
    )


def apply_scene_payload(scene: Scene, payload: SceneWrite) -> None:
    scene.name = payload.name
    scene.description = payload.description
    scene.icon = payload.icon
    scene.color = payload.color
    scene.trigger_type = payload.trigger_type
    scene.trigger_label = payload.trigger_label
    scene.room_names = json.dumps(payload.room_labels, ensure_ascii=False)
    device_ids = set(payload.device_ids) | {step.device_id for step in payload.steps}
    scene.device_count = len(device_ids)
    scene.enabled = payload.enabled
    scene.recommended = payload.recommended
    values = [payload.name, *(step.device_id for step in payload.steps)]
    scene.high_risk = (
        payload.high_risk
        if payload.high_risk is not None
        else any(
            keyword in value.lower()
            for value in values
            for keyword in HIGH_RISK_KEYWORDS
        )
    )
    scene.updated_at = now_utc()


def replace_steps(scene: Scene, payload: SceneWrite) -> None:
    scene.steps.clear()
    scene.steps.extend(
        SceneStep(
            id=f"{scene.id}-{step.order}-{uuid4().hex[:6]}",
            name=step.name,
            description=step.description,
            device_id=step.device_id,
            step_order=step.order,
        )
        for step in sorted(payload.steps, key=lambda item: item.order)
    )


def get_scenes_service(
    db: Session,
    household_id: int,
    keyword: str | None,
    trigger_type: str | None,
    enabled: str,
    room_id: int | None = None,
) -> SceneListRead:
    filters = [Scene.household_id == household_id]
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Scene.name.like(term),
                Scene.description.like(term),
                Scene.trigger_label.like(term),
            )
        )
    if trigger_type:
        filters.append(Scene.trigger_type == trigger_type)
    if enabled == "enabled":
        filters.append(Scene.enabled.is_(True))
    elif enabled == "disabled":
        filters.append(Scene.enabled.is_(False))

    query = select(Scene)
    if room_id is not None:
        query = query.join(SceneRoom, SceneRoom.scene_id == Scene.id).where(
            SceneRoom.room_id == room_id
        )
    scenes = db.scalars(
        query.options(selectinload(Scene.steps))
        .where(*filters)
        .order_by(Scene.sort_order, Scene.updated_at.desc())
    ).all()
    return SceneListRead(
        items=[serialize_scene(scene) for scene in scenes], total=len(scenes)
    )


def replace_scene_rooms(
    db: Session, scene: Scene, household_id: int, room_labels: list[str]
) -> None:
    labels = set(room_labels)
    rooms = (
        list(
            db.scalars(
                select(Room).where(
                    Room.household_id == household_id,
                    Room.name.in_(labels),
                )
            )
        )
        if labels
        else []
    )
    found_labels = {room.name for room in rooms}
    if found_labels != labels:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "部分房间不存在",
                "rooms": sorted(labels - found_labels),
            },
        )
    db.execute(delete(SceneRoom).where(SceneRoom.scene_id == scene.id))
    db.add_all([SceneRoom(scene_id=scene.id, room_id=room.id) for room in rooms])


def add_scene_service(
    db: Session, household_id: int, user_id: int, payload: SceneWrite
) -> SceneRead:
    base_id = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")[:40]
    base_id = base_id or "scene"
    scene_id = base_id
    while db.scalar(
        select(Scene.id).where(Scene.household_id == household_id, Scene.id == scene_id)
    ):
        scene_id = f"{base_id}-{uuid4().hex[:8]}"
    scene = Scene(
        id=scene_id,
        household_id=household_id,
        created_by=user_id,
    )
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    db.add(scene)
    replace_scene_rooms(db, scene, household_id, payload.room_labels)
    scene.sort_order = (
        db.scalar(
            select(func.max(Scene.sort_order)).where(Scene.household_id == household_id)
        )
        or 0
    )
    scene.sort_order += 10
    db.commit()
    db.refresh(scene)
    return serialize_scene(get_scene_or_404(db, household_id, scene.id))


def edit_scene_service(
    db: Session, household_id: int, scene_id: str, payload: SceneWrite
) -> SceneRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    replace_scene_rooms(db, scene, household_id, payload.room_labels)
    db.commit()
    return serialize_scene(get_scene_or_404(db, household_id, scene.id))


def change_enabled_service(
    db: Session, household_id: int, scene_id: str, enabled: bool
) -> Scene:
    scene = get_scene_or_404(db, household_id, scene_id)
    scene.enabled = enabled
    scene.updated_at = now_utc()
    db.commit()
    db.refresh(scene)
    return scene


# === 场景执行 ===


def run_scene_service(
    db: Session,
    household_id: int,
    scene_id: str,
    confirm_high_risk: bool,
    source: str,
) -> SceneExecutionRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    if scene.high_risk and not confirm_high_risk:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该场景包含高风险动作，请确认后执行",
        )
    if not scene.enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="场景已停用")

    started_at = now_utc()
    execution_id = f"exec-{started_at:%Y%m%d%H%M%S}-{uuid4().hex[:8]}"
    log = SceneExecutionLog(
        id=execution_id,
        scene_id=scene.id,
        status="enabled",
        source=source,
        started_at=started_at,
        finished_at=started_at,
        message="执行成功",
    )
    log.steps = [
        SceneExecutionStep(
            id=f"{execution_id}-{index}",
            step_id=step.id,
            status="completed",
            started_at=started_at,
            finished_at=started_at,
            message=f"{step.name}成功",
        )
        for index, step in enumerate(scene.steps, 1)
    ]
    scene.monthly_execute_count += 1
    scene.last_executed_at = started_at
    scene.updated_at = started_at
    db.add(log)
    db.commit()
    return serialize_execution(log)


def serialize_execution(log: SceneExecutionLog) -> SceneExecutionRead:
    return SceneExecutionRead(
        execution_id=log.id,
        scene_id=log.scene_id,
        status=log.status,
        started_at=log.started_at,
        finished_at=log.finished_at,
        steps=[
            SceneExecutionStepRead(
                step_id=step.step_id, status=step.status, message=step.message
            )
            for step in log.steps
        ],
    )


def duplicate_scene_service(
    db: Session, household_id: int, user_id: int, scene_id: str, name: str
) -> SceneRead:
    source = get_scene_or_404(db, household_id, scene_id)
    payload = SceneWrite(
        name=name,
        description=source.description,
        icon=source.icon,
        color=source.color,
        trigger_type=cast(TriggerType, source.trigger_type),
        trigger_label=source.trigger_label,
        room_labels=parse_json_list(source.room_names),
        enabled=source.enabled,
        recommended=False,
        high_risk=source.high_risk,
        steps=[
            {
                "name": step.name,
                "description": step.description,
                "device_id": step.device_id,
                "order": step.step_order,
            }
            for step in source.steps
        ],
    )
    return add_scene_service(db, household_id, user_id, payload)


def remove_scene_service(db: Session, household_id: int, scene_id: str) -> None:
    """删除场景及其执行步骤、执行日志（ORM 级联清理辅助表）。"""
    scene = get_scene_or_404(db, household_id, scene_id)
    db.delete(scene)
    db.commit()


def get_logs_service(
    db: Session, household_id: int, scene_id: str, limit: int
) -> SceneLogListRead:
    get_scene_or_404(db, household_id, scene_id)
    logs = db.scalars(
        select(SceneExecutionLog)
        .where(SceneExecutionLog.scene_id == scene_id)
        .order_by(SceneExecutionLog.started_at.desc())
        .limit(limit)
    ).all()
    return SceneLogListRead(
        items=[SceneLogRead.model_validate(log, from_attributes=True) for log in logs]
    )


def get_summary_service(db: Session, household_id: int) -> SceneSummaryRead:
    total, enabled, manual = db.execute(
        select(
            func.count(Scene.id),
            func.count().filter(Scene.enabled.is_(True)),
            func.count().filter(Scene.trigger_type == "manual"),
        ).where(Scene.household_id == household_id)
    ).one()
    automation = total - manual
    month_start = now_utc().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly = (
        db.scalar(
            select(func.count())
            .select_from(SceneExecutionLog)
            .join(Scene, Scene.id == SceneExecutionLog.scene_id)
            .where(
                Scene.household_id == household_id,
                SceneExecutionLog.started_at >= month_start,
            )
        )
        or 0
    )
    return SceneSummaryRead(
        enabled=enabled,
        automation=automation,
        manual=manual,
        monthly_executions=monthly,
        enabled_rate=round(enabled * 100 / total, 1) if total else 0,
        automation_rate=round(automation * 100 / total, 1) if total else 0,
        manual_rate=round(manual * 100 / total, 1) if total else 0,
        monthly_growth_rate=0,
    )


def reorder_scenes_service(
    db: Session, household_id: int, payload: SceneOrderWrite
) -> SceneOrderRead:
    ids = [item.id for item in payload.items]
    found_ids = set(
        db.scalars(
            select(Scene.id).where(
                Scene.household_id == household_id, Scene.id.in_(ids)
            )
        )
    )
    missing = set(ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="部分场景不存在"
        )
    order_by_id = {item.id: item.sort_order for item in payload.items}
    db.execute(
        update(Scene)
        .where(Scene.household_id == household_id, Scene.id.in_(ids))
        .values(sort_order=case(order_by_id, value=Scene.id))
    )
    db.commit()
    return SceneOrderRead(updated=len(payload.items))


def get_scene_preview_service(
    db: Session, household_id: int, scene_id: str
) -> ScenePreviewRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    return ScenePreviewRead(
        scene_id=scene.id,
        high_risk=scene.high_risk,
        trigger_label=scene.trigger_label,
        steps=[
            ScenePreviewStep(
                step_id=step.id,
                name=step.name,
                device_id=step.device_id,
                estimated_ms=300,
                risk_level=(
                    "high"
                    if any(
                        word in step.device_id.lower() for word in HIGH_RISK_KEYWORDS
                    )
                    else "low"
                ),
            )
            for step in scene.steps
        ],
    )


def get_execution_service(
    db: Session, household_id: int, execution_id: str
) -> SceneExecutionRead:
    log = db.scalar(
        select(SceneExecutionLog)
        .options(selectinload(SceneExecutionLog.steps))
        .join(Scene, Scene.id == SceneExecutionLog.scene_id)
        .where(
            Scene.household_id == household_id,
            SceneExecutionLog.id == execution_id,
        )
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在"
        )
    return serialize_execution(log)


# === 场景模板 ===


def serialize_template(template: SceneTemplate) -> SceneTemplateRead:
    raw_steps = parse_json_list(template.steps_json)
    return SceneTemplateRead(
        id=template.id,
        name=template.name,
        description=template.description,
        icon=template.icon,
        color=template.color,
        trigger_type=cast(TriggerType, template.trigger_type),
        trigger_label=template.trigger_label,
        room_labels=parse_json_list(template.room_labels),
        device_count=template.device_count,
        recommended=template.recommended,
        category=template.category,
        steps=[
            {
                "id": step.get("id", f"{template.id}-{index}"),
                "name": step["name"],
                "description": step.get("description", ""),
                "device_id": step["deviceId"],
                "order": step.get("order", index),
            }
            for index, step in enumerate(raw_steps, 1)
        ],
    )


def get_templates_service(
    db: Session, keyword: str | None, category: str | None, limit: int
) -> SceneTemplateListRead:
    filters = [SceneTemplate.enabled.is_(True)]
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        filters.append(
            or_(SceneTemplate.name.like(term), SceneTemplate.description.like(term))
        )
    if category:
        filters.append(SceneTemplate.category == category)
    templates = db.scalars(
        select(SceneTemplate)
        .where(*filters)
        .order_by(SceneTemplate.sort_order, SceneTemplate.updated_at.desc())
        .limit(limit)
    ).all()
    return SceneTemplateListRead(items=[serialize_template(item) for item in templates])


def import_template_service(
    db: Session,
    household_id: int,
    user_id: int,
    template_id: str,
    payload: SceneTemplateUseWrite,
) -> SceneRead:
    template = get_template_or_404(db, template_id)
    data = serialize_template(template)
    scene_payload = SceneWrite(
        name=payload.name or template.name,
        description=template.description,
        icon=template.icon,
        color=template.color,
        trigger_type=cast(TriggerType, template.trigger_type),
        trigger_label=template.trigger_label,
        room_labels=data.room_labels,
        enabled=payload.enabled,
        recommended=False,
        steps=[
            {
                "name": step.name,
                "description": step.description,
                "device_id": payload.device_mapping.get(step.device_id, step.device_id),
                "order": step.order,
            }
            for step in data.steps
        ],
    )
    result = add_scene_service(db, household_id, user_id, scene_payload)
    scene = db.get(Scene, result.id)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="创建的场景未找到"
        )
    scene.source_template_id = template.id
    db.commit()
    return serialize_scene(get_scene_or_404(db, household_id, result.id))


def get_template_preview_service(
    db: Session, household_id: int, template_id: str
) -> SceneTemplatePreviewRead:
    template = serialize_template(get_template_or_404(db, template_id))
    known_ids = set(
        db.scalars(
            select(Device.device_id).where(Device.household_id == household_id)
        ).all()
    )
    steps = [
        SceneTemplatePreviewStep(
            name=step.name,
            description=step.description,
            device_id=step.device_id,
            matched=step.device_id in known_ids,
        )
        for step in template.steps
    ]
    matched = sum(step.matched for step in steps)
    return SceneTemplatePreviewRead(
        template_id=template_id,
        matched_device_count=matched,
        missing_device_count=len(steps) - matched,
        steps=steps,
    )


def add_draft_service(
    db: Session, household_id: int, user_id: int, payload: SceneDraftWrite
) -> SceneDraftRead:
    draft = SceneDraft(
        id=f"draft-{uuid4().hex}",
        household_id=household_id,
        created_by=user_id,
        payload_json=payload.model_dump_json(by_alias=True),
        updated_at=now_utc(),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return SceneDraftRead(draft_id=draft.id, updated_at=draft.updated_at)


# === 批量操作 ===


def batch_change_enabled_service(
    db: Session, household_id: int, payload: SceneBatchEnabledWrite
) -> SceneBatchEnabledResult:
    """批量启用或停用场景。空列表时操作全部场景。"""
    filters = [Scene.household_id == household_id]
    if payload.scene_ids:
        filters.append(Scene.id.in_(payload.scene_ids))
    result = cast(
        CursorResult[Any],
        db.execute(
            update(Scene)
            .where(*filters)
            .values(enabled=payload.enabled, updated_at=now_utc())
        ),
    )
    db.commit()
    return SceneBatchEnabledResult(updated_count=result.rowcount or 0)


def batch_set_schedule_service(
    db: Session, household_id: int, payload: SceneBatchScheduleWrite
) -> SceneBatchScheduleResult:
    """批量设置场景的触发类型和定时触发描述。空列表时操作全部场景。"""
    filters = [Scene.household_id == household_id]
    if payload.scene_ids:
        filters.append(Scene.id.in_(payload.scene_ids))
    result = cast(
        CursorResult[Any],
        db.execute(
            update(Scene)
            .where(*filters)
            .values(
                trigger_type=payload.trigger_type,
                trigger_label=payload.trigger_label,
                updated_at=now_utc(),
            )
        ),
    )
    db.commit()
    return SceneBatchScheduleResult(updated_count=result.rowcount or 0)
