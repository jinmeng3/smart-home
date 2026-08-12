from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.agent_service.runner import run_agent
from app.agents.context import agent_context
from app.agents.errors import AgentModelNotFound
from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.agent import AgentRunRequest
from app.services.chat import get_chat_session

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/runs")
def agent_run(
    payload: AgentRunRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    ctx = agent_context(
        household_id=payload.household_id,
        session_id=payload.session_id,
        db=db,
        current_user=current_user,
    )
    get_chat_session(
        db=db, current_user=current_user, session_id=payload.session_id, messages=[]
    )
    # 校验数据库种的模型是否越界
    if payload.model:
        model_config = db.scalar(select(AIModel).where(AIModel.name == payload.model))

        if model_config is None or model_config.user_id != current_user.id:
            raise AgentModelNotFound("模型未找到")
    else:
        model_config = db.scalar(
            select(AIModel).where(
                AIModel.user_id == current_user.id, AIModel.is_active.is_(True)
            )
        )
        if model_config is None:
            raise AgentModelNotFound("模型未启用")

    if not model_config.is_active:
        raise AgentModelNotFound("该模型已停用")

    return StreamingResponse(
        run_agent(
            context=ctx,
            household_name=payload.household_name,
            message=payload.message,
            model_config=model_config,
            db=db,
        ),
        media_type="text/event-stream",
    )
