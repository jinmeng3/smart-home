from app.agents.risk import classify_scene_execution
from app.services.scene import run_scene_service


def execute_scene_operation(db, context, args, pending) -> dict:
    """执行场景操作。"""
    scene_id = args.get("scene_id", "")
    idempotency_key = pending.get("approval_id")

    # 执行前重新读取资源并重新分类
    current = classify_scene_execution(
        db=db,
        context=context,
        scene_id=scene_id,
    )

    if current.resource_version != pending.get("resource_version"):
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_APPROVAL_STALE",
            "error": "场景在确认后已发生变化，请重新预览并确认",
        }

    execution = run_scene_service(
        db=db,
        household_id=context.household_id,
        scene_id=scene_id,
        confirm_high_risk=True,
        source="agent",
        idempotency_key=idempotency_key,
    )

    return {
        "ok": True,
        "status": "submitted",
        "execution_id": execution.execution_id,
        "scene_id": execution.scene_id,
        "message": "场景已提交到业务执行层，尚未完成设备状态回读验证",
    }