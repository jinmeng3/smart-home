import json
import re
from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.device import Device
from app.models.scene import (
    Scene,
    SceneDraft,
    SceneExecutionLog,
    SceneExecutionStep,
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:40] or "scene"


def unique_scene_id(db: Session, name: str) -> str:
    base = slugify(name)
    candidate = base
    while db.get(Scene, candidate):
        candidate = f"{base}-{uuid4().hex[:8]}"
    return candidate


def get_scene_or_404(db: Session, scene_id: str) -> Scene:
    scene = db.scalar(
        select(Scene).options(selectinload(Scene.steps)).where(Scene.id == scene_id)
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


def detect_high_risk(payload: SceneWrite) -> bool:
    if payload.high_risk is not None:
        return payload.high_risk
    values = [payload.name, *(step.device_id for step in payload.steps)]
    return any(
        keyword in value.lower() for value in values for keyword in HIGH_RISK_KEYWORDS
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
    scene.high_risk = detect_high_risk(payload)
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
    db: Session, keyword: str | None, trigger_type: str | None, enabled: str
) -> SceneListRead:
    filters = []
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

    scenes = db.scalars(
        select(Scene)
        .options(selectinload(Scene.steps))
        .where(*filters)
        .order_by(Scene.sort_order, Scene.updated_at.desc())
    ).all()
    return SceneListRead(
        items=[serialize_scene(scene) for scene in scenes], total=len(scenes)
    )


def add_scene_service(db: Session, payload: SceneWrite) -> SceneRead:
    scene = Scene(id=unique_scene_id(db, payload.name))
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    scene.sort_order = db.scalar(select(func.max(Scene.sort_order))) or 0
    scene.sort_order += 10
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return serialize_scene(get_scene_or_404(db, scene.id))


def edit_scene_service(db: Session, scene_id: str, payload: SceneWrite) -> SceneRead:
    scene = get_scene_or_404(db, scene_id)
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    db.commit()
    return serialize_scene(get_scene_or_404(db, scene.id))


def change_enabled_service(db: Session, scene_id: str, enabled: bool) -> Scene:
    scene = get_scene_or_404(db, scene_id)
    scene.enabled = enabled
    scene.updated_at = now_utc()
    db.commit()
    db.refresh(scene)
    return scene


# === 场景执行 ===


def run_scene_service(
    db: Session, scene_id: str, confirm_high_risk: bool, source: str
) -> SceneExecutionRead:
    scene = get_scene_or_404(db, scene_id)
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


def duplicate_scene_service(db: Session, scene_id: str, name: str) -> SceneRead:
    source = get_scene_or_404(db, scene_id)
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
    return add_scene_service(db, payload)


def remove_scene_service(db: Session, scene_id: str) -> None:
    """删除场景及其执行步骤、执行日志（ORM 级联清理辅助表）。"""
    scene = get_scene_or_404(db, scene_id)
    db.delete(scene)
    db.commit()


def get_logs_service(db: Session, scene_id: str, limit: int) -> SceneLogListRead:
    get_scene_or_404(db, scene_id)
    logs = db.scalars(
        select(SceneExecutionLog)
        .where(SceneExecutionLog.scene_id == scene_id)
        .order_by(SceneExecutionLog.started_at.desc())
        .limit(limit)
    ).all()
    return SceneLogListRead(
        items=[SceneLogRead.model_validate(log, from_attributes=True) for log in logs]
    )


def get_summary_service(db: Session) -> SceneSummaryRead:
    total = db.scalar(select(func.count()).select_from(Scene)) or 0
    enabled = (
        db.scalar(
            select(func.count()).select_from(Scene).where(Scene.enabled.is_(True))
        )
        or 0
    )
    manual = (
        db.scalar(
            select(func.count())
            .select_from(Scene)
            .where(Scene.trigger_type == "manual")
        )
        or 0
    )
    automation = total - manual
    month_start = now_utc().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly = (
        db.scalar(
            select(func.count())
            .select_from(SceneExecutionLog)
            .where(SceneExecutionLog.started_at >= month_start)
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


def reorder_scenes_service(db: Session, payload: SceneOrderWrite) -> SceneOrderRead:
    ids = [item.id for item in payload.items]
    scenes = {
        scene.id: scene for scene in db.scalars(select(Scene).where(Scene.id.in_(ids)))
    }
    missing = set(ids) - scenes.keys()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="部分场景不存在"
        )
    for item in payload.items:
        scenes[item.id].sort_order = item.sort_order
    db.commit()
    return SceneOrderRead(updated=len(payload.items))


def get_scene_preview_service(db: Session, scene_id: str) -> ScenePreviewRead:
    scene = get_scene_or_404(db, scene_id)
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


def get_execution_service(db: Session, execution_id: str) -> SceneExecutionRead:
    log = db.scalar(
        select(SceneExecutionLog)
        .options(selectinload(SceneExecutionLog.steps))
        .where(SceneExecutionLog.id == execution_id)
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
    db: Session, template_id: str, payload: SceneTemplateUseWrite
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
    result = add_scene_service(db, scene_payload)
    scene = db.get(Scene, result.id)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="创建的场景未找到"
        )
    scene.source_template_id = template.id
    db.commit()
    return serialize_scene(get_scene_or_404(db, result.id))


def get_template_preview_service(db: Session, template_id: str) -> SceneTemplatePreviewRead:
    template = serialize_template(get_template_or_404(db, template_id))
    known_ids = set(db.scalars(select(Device.device_id)).all())
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


def add_draft_service(db: Session, payload: SceneDraftWrite) -> SceneDraftRead:
    draft = SceneDraft(
        id=f"draft-{uuid4().hex}",
        payload_json=payload.model_dump_json(by_alias=True),
        updated_at=now_utc(),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return SceneDraftRead(draft_id=draft.id, updated_at=draft.updated_at)


# === 批量操作 ===


def batch_change_enabled_service(
    db: Session, payload: SceneBatchEnabledWrite
) -> SceneBatchEnabledResult:
    """批量启用或停用场景。空列表时操作全部场景。"""
    query = select(Scene)
    if payload.scene_ids:
        query = query.where(Scene.id.in_(payload.scene_ids))
    scenes = list(db.scalars(query).all())
    now = now_utc()
    for scene in scenes:
        scene.enabled = payload.enabled
        scene.updated_at = now
    db.commit()
    return SceneBatchEnabledResult(updated_count=len(scenes))


def batch_set_schedule_service(
    db: Session, payload: SceneBatchScheduleWrite
) -> SceneBatchScheduleResult:
    """批量设置场景的触发类型和定时触发描述。空列表时操作全部场景。"""
    query = select(Scene)
    if payload.scene_ids:
        query = query.where(Scene.id.in_(payload.scene_ids))
    scenes = list(db.scalars(query).all())
    now = now_utc()
    for scene in scenes:
        scene.trigger_type = payload.trigger_type
        scene.trigger_label = payload.trigger_label
        scene.updated_at = now
    db.commit()
    return SceneBatchScheduleResult(updated_count=len(scenes))
