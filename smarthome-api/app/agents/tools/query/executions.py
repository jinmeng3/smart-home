from app.agents.context import AgentContext
from app.core.config import get_settings
from app.models.automation import Automation, AutomationExecution
from app.models.device import Device, DeviceLog
from app.models.scene import Scene, SceneExecutionLog
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListDeviceLogsInput(BaseModel):
    """查询设备日志的筛选参数。"""

    device_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=10, ge=1)


class ListSceneExecutionsInput(BaseModel):
    """查询场景执行记录的筛选参数。"""

    scene_id: str | None = Field(default=None, min_length=1, max_length=64)
    limit: int = Field(default=10, ge=1)


class ListAutomationExecutionsInput(BaseModel):
    """查询自动化执行记录的筛选参数。"""

    automation_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=10, ge=1)


def _limit(value: int) -> int:
    """限制查询条数不超过配置上限。"""
    return min(value, get_settings().agent_tool_result_max_length)


def _to_iso(value):
    """将 datetime 转为 ISO 格式字符串，None 则原样返回。"""
    return value.isoformat() if value else None


def list_device_logs(db: Session, context: AgentContext, device_id=None, limit=10):
    """查询设备日志，可按 device_id 筛选，按时间倒序。返回 id、设备名称、操作、消息、创建时间。"""
    query = (
        select(DeviceLog, Device.name)
        .join(Device, Device.id == DeviceLog.device_id)
        .where(Device.household_id == context.household_id)
    )
    if device_id is not None:
        query = query.where(DeviceLog.device_id == device_id)
    rows = db.execute(
        query.order_by(DeviceLog.created_at.desc()).limit(_limit(limit))
    ).all()
    return [
        {
            "id": log.id,
            "device_id": log.device_id,
            "device_name": name,
            "action": log.action,
            "message": log.message,
            "created_at": _to_iso(log.created_at),
        }
        for log, name in rows
    ]


def list_scene_executions(db: Session, context: AgentContext, scene_id=None, limit=10):
    """查询场景执行记录，可按 scene_id 筛选，按开始时间倒序。返回 id、场景名称、状态、来源、消息、开始/结束时间。"""
    query = (
        select(SceneExecutionLog, Scene.name)
        .join(Scene, Scene.id == SceneExecutionLog.scene_id)
        .where(Scene.household_id == context.household_id)
    )
    if scene_id:
        query = query.where(SceneExecutionLog.scene_id == scene_id)
    rows = db.execute(
        query.order_by(SceneExecutionLog.started_at.desc()).limit(_limit(limit))
    ).all()
    return [
        {
            "id": log.id,
            "scene_id": log.scene_id,
            "scene_name": name,
            "status": log.status,
            "source": log.source,
            "message": log.message,
            "started_at": _to_iso(log.started_at),
            "finished_at": _to_iso(log.finished_at),
        }
        for log, name in rows
    ]


def list_automation_executions(
    db: Session, context: AgentContext, automation_id=None, limit=10
):
    """查询自动化执行记录，可按 automation_id 筛选，按开始时间倒序。返回 id、自动化名称、状态、来源、耗时、错误信息、开始/结束时间。"""
    query = (
        select(AutomationExecution, Automation.name)
        .join(Automation, Automation.id == AutomationExecution.automation_id)
        .where(Automation.household_id == context.household_id)
    )
    if automation_id is not None:
        query = query.where(AutomationExecution.automation_id == automation_id)
    rows = db.execute(
        query.order_by(AutomationExecution.started_at.desc()).limit(_limit(limit))
    ).all()
    return [
        {
            "id": log.id,
            "automation_id": log.automation_id,
            "automation_name": name,
            "status": log.status,
            "source": log.source,
            "duration_ms": log.duration_ms,
            "error_message": log.error_message,
            "started_at": _to_iso(log.started_at),
            "finished_at": _to_iso(log.finished_at),
        }
        for log, name in rows
    ]
