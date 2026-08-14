from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.agents.risk import classify_scene_execution
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class PreviewSceneInput(BaseModel):
    scene_id: str = Field(min_length=1, max_length=64)


def preview_scene(
    db: Session,
    context: AgentContext,
    scene_id: str,
):
    """预览当前家庭中的场景动作和风险，不执行任何设备操作。"""
    try:
        decision = classify_scene_execution(db, context, scene_id)
    except HTTPException as exc:
        raise AgentToolExecutionError(str(exc.detail)) from exc

    return {
        "status": "previewed",
        "risk_level": decision.level,
        "requires_approval": decision.requires_approval,
        "reasons": decision.reasons,
        "resource_version": decision.resource_version,
        **decision.preview,
    }
