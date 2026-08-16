from app.schemas.automation import (
    ActionWrite,
    AutomationCreate,
    AutomationUpdate,
    ConditionWrite,
    FlowItem,
)
from app.services.automation import (
    create_automation_service,
    delete_automation_service,
    update_automation_service,
)
from app.services.automation import (
    get_automation as get_automation_service,
)
from pydantic import BaseModel, Field


class CreateAutomationInput(BaseModel):
    """创建自动化规则的参数。"""

    name: str = Field(min_length=1, max_length=30)
    description: str = Field(default="", max_length=100)
    triggers: list[dict] = Field(min_length=1)
    conditions: list[dict] = Field(default_factory=list)
    actions: list[dict] = Field(min_length=1, max_length=50)
    priority: int = Field(default=2, ge=1, le=3)
    cooldown_seconds: int = Field(default=0, ge=0)
    delay_seconds: int = Field(default=0, ge=0)
    note: str = Field(default="", max_length=100)


class UpdateAutomationInput(BaseModel):
    """更新自动化规则的参数。至少提供一个更新字段。"""

    automation_id: int
    version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = Field(default=None, max_length=100)
    triggers: list[dict] | None = None
    conditions: list[dict] | None = None
    actions: list[dict] | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    cooldown_seconds: int | None = Field(default=None, ge=0)
    delay_seconds: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=100)


class SetAutomationEnabledInput(BaseModel):
    """启用或停用自动化规则的参数。"""

    automation_id: int
    enabled: bool


class DeleteAutomationInput(BaseModel):
    """删除自动化规则的参数。"""

    automation_id: int


# === 执行函数（由 graph/execute.py 调用）===


def create_automation_operation(db, context, args) -> dict:
    """创建自动化规则。"""
    try:
        payload = AutomationCreate(
            name=args["name"],
            description=args.get("description", ""),
            triggers=[
                FlowItem(type=t["type"], config=t.get("config", {}))
                for t in args.get("triggers", [])
            ],
            conditions=[
                ConditionWrite(
                    type=c["type"],
                    config=c.get("config", {}),
                    position=c.get("position", index),
                )
                for index, c in enumerate(args.get("conditions", []))
            ],
            actions=[
                ActionWrite(
                    type=a["type"],
                    config=a.get("config", {}),
                    position=a.get("position", index),
                    device_id=a.get("device_id"),
                    scene_id=a.get("scene_id"),
                )
                for index, a in enumerate(args.get("actions", []))
            ],
            priority=args.get("priority", 2),
            cooldown_seconds=args.get("cooldown_seconds", 0),
            delay_seconds=args.get("delay_seconds", 0),
            note=args.get("note", ""),
        )
        result = create_automation_service(
            db=db,
            household_id=context.household_id,
            user_id=context.user_id,
            payload=payload,
        )
        return {
            "ok": True,
            "status": "created",
            "automation_id": result.id,
            "automation_name": result.name,
            "version": result.version,
            "message": f"自动化规则「{result.name}」已创建",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": f"创建自动化失败：{e!s}",
        }


def update_automation_operation(db, context, args) -> dict:
    """更新自动化规则。"""
    try:
        automation_id = args["automation_id"]
        update_kwargs: dict = {
            "name": args.get("name"),
            "description": args.get("description"),
            "priority": args.get("priority"),
            "cooldown_seconds": args.get("cooldown_seconds"),
            "delay_seconds": args.get("delay_seconds"),
            "note": args.get("note"),
        }
        update_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}

        if args.get("triggers") is not None:
            update_kwargs["triggers"] = [
                FlowItem(type=t["type"], config=t.get("config", {}))
                for t in args["triggers"]
            ]
        if args.get("conditions") is not None:
            update_kwargs["conditions"] = [
                ConditionWrite(
                    type=c["type"],
                    config=c.get("config", {}),
                    position=c.get("position", index),
                )
                for index, c in enumerate(args["conditions"])
            ]
        if args.get("actions") is not None:
            update_kwargs["actions"] = [
                ActionWrite(
                    type=a["type"],
                    config=a.get("config", {}),
                    position=a.get("position", index),
                    device_id=a.get("device_id"),
                    scene_id=a.get("scene_id"),
                )
                for index, a in enumerate(args["actions"])
            ]

        payload = AutomationUpdate(version=args.get("version", 1), **update_kwargs)
        result = update_automation_service(
            db=db,
            automation_id=automation_id,
            household_id=context.household_id,
            payload=payload,
        )
        return {
            "ok": True,
            "status": "updated",
            "automation_id": result.id,
            "automation_name": result.name,
            "version": result.version,
            "message": f"自动化规则「{result.name}」已更新",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": f"更新自动化失败：{e!s}",
        }


def set_automation_enabled_operation(db, context, args) -> dict:
    """启用或停用自动化规则。"""
    try:
        automation_id = args["automation_id"]
        enabled = args.get("enabled", True)

        automation = get_automation_service(db, automation_id, context.household_id)
        automation.enabled = enabled
        db.commit()

        return {
            "ok": True,
            "status": "updated",
            "automation_id": automation.id,
            "automation_name": automation.name,
            "enabled": enabled,
            "message": f"自动化规则「{automation.name}」已{'启用' if enabled else '停用'}",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": f"切换自动化状态失败：{e!s}",
        }


def delete_automation_operation(db, context, args) -> dict:
    """删除自动化规则。"""
    try:
        automation_id = args["automation_id"]
        automation = get_automation_service(db, automation_id, context.household_id)
        name = automation.name
        delete_automation_service(db, automation_id, context.household_id)

        return {
            "ok": True,
            "status": "deleted",
            "automation_id": automation_id,
            "automation_name": name,
            "message": f"自动化规则「{name}」已删除",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": f"删除自动化失败：{e!s}",
        }
