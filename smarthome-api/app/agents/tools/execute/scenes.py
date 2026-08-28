from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.risk import classify_scene_execution
from app.models.device import Device
from app.services.scene import run_scene_service


class ExecuteSceneInput(BaseModel):
    """执行场景的参数。"""

    scene_id: str = Field(min_length=1, max_length=64)


def _stale_result(error: str) -> dict:
    return {
        "ok": False,
        "status": "failed",
        "code": "AGENT_APPROVAL_STALE",
        "error": error,
    }


def execute_scene_operation(db, context, args, pending) -> dict:
    """执行场景操作，并在执行后验证设备状态变更。

    执行前重新读取场景做二次校验：场景被删除、停用或版本变化时，
    统一返回 ``AGENT_APPROVAL_STALE``，避免把“审批失效”混同为泛化错误。
    """
    scene_id = args.get("scene_id", "")
    idempotency_key = pending.get("approval_id")

    try:
        current = classify_scene_execution(
            db=db,
            context=context,
            scene_id=scene_id,
        )
    except HTTPException:
        # 场景在审批期间被删除或不属于当前家庭
        return _stale_result("场景已不存在，请重新预览并确认")

    target_device_ids = {
        step["device_id"]
        for step in current.preview.get("steps", [])
        if step.get("device_id")
    }
    before_devices = _get_device_status_snapshot(
        db, context.household_id, target_device_ids
    )

    if current.resource_version != pending.get("resource_version"):
        return _stale_result("场景在确认后已发生变化，请重新预览并确认")

    try:
        execution = run_scene_service(
            db=db,
            household_id=context.household_id,
            scene_id=scene_id,
            confirm_high_risk=True,
            source="agent",
            executed_by=context.user_id,
            session_id=context.session_id,
            auto_execute_low_risk=context.auto_execute_low_risk,
            idempotency_key=idempotency_key,
        )
    except HTTPException:
        # 场景在审批期间被停用（run_scene_service 抛 409）
        return _stale_result("场景已不可执行，请重新预览并确认")

    readback = _verify_device_readback(db, context.household_id, before_devices)

    return {
        "ok": True,
        "status": "submitted",
        "verified": False,
        "execution_id": execution.execution_id,
        "scene_id": execution.scene_id,
        "message": (
            "场景已提交，观察到目标设备状态变化，但尚未验证是否达到目标状态"
            if readback["changed"]
            else "场景已提交，暂未观察到目标设备状态变化"
        ),
        "device_readback": readback,
    }


def _get_device_status_snapshot(
    db: Session, household_id: int, device_ids: set[str]
) -> dict[str, str]:
    """仅获取场景目标设备状态，避免无关设备变化造成误判。"""
    if not device_ids:
        return {}
    devices = db.scalars(
        select(Device).where(
            Device.household_id == household_id,
            Device.device_id.in_(device_ids),
        )
    ).all()
    return {device.device_id: device.status.value for device in devices}


def _verify_device_readback(
    db: Session, household_id: int, before: dict[str, str]
) -> dict:
    """验证设备状态在执行后是否发生变化。"""
    after = _get_device_status_snapshot(db, household_id, set(before))

    changed_devices = []
    for device_id, status_before in before.items():
        status_after = after.get(device_id)
        if status_after != status_before:
            changed_devices.append(
                {
                    "device_id": device_id,
                    "status_before": status_before,
                    "status_after": status_after,
                }
            )

    return {
        "changed": len(changed_devices) > 0,
        "changed_count": len(changed_devices),
        "devices": changed_devices,
    }
