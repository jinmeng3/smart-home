from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.core.config import get_settings
from app.models.scene import Scene
from app.services.scene import get_scene_or_404, get_scenes_service, serialize_scene
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListScenesInput(BaseModel):
    """列出场景的筛选参数。"""

    keyword: str | None = Field(default=None, max_length=80)
    enabled: str | None = Field(default=None, pattern="^(enabled|disabled)$")
    trigger_type: str | None = Field(default=None, max_length=20)


def list_scenes(
    db: Session, context: AgentContext, keyword=None, enabled=None, trigger_type=None
):
    """列出当前家庭的场景，可按关键词、启用状态、触发类型筛选。返回场景列表含 id、名称、描述、触发类型、启用状态等。"""
    result = get_scenes_service(
        db, context.household_id, keyword, trigger_type, enabled or "all"
    )
    limit = get_settings().agent_tool_result_max_length
    return [item.model_dump(mode="json") for item in result.items[:limit]]


class GetSceneInput(BaseModel):
    """获取单个场景的参数。scene_id 和 name 至少提供一个。"""

    scene_id: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=80)


def get_scene(db: Session, context: AgentContext, scene_id=None, name=None):
    """获取指定场景详情及其步骤。scene_id 或 name 至少提供一个，优先按 scene_id 查找。"""
    if not scene_id and not name:
        raise AgentToolExecutionError("scene_id 或 name 至少提供一个")
    if not scene_id:
        scene_id = db.scalar(
            select(Scene.id).where(
                Scene.household_id == context.household_id, Scene.name == name
            )
        )
    if not scene_id:
        raise AgentToolExecutionError("场景不存在")
    try:
        return serialize_scene(
            get_scene_or_404(db, context.household_id, scene_id)
        ).model_dump(mode="json")
    except HTTPException as exc:
        raise AgentToolExecutionError(str(exc.detail)) from exc
