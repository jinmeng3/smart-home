from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.agent_service.resumer import agent_thread_id, resume_agent
from app.agents.agent_service.runner import run_agent
from app.agents.checkpointer import get_checkpointer
from app.agents.context import agent_context
from app.agents.errors import AgentModelNotFound
from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.ai import AIModel
from app.models.user import User
from app.schemas.agent import (
    AgentDecisionRequest,
    AgentRunRequest,
    PendingApprovalRead,
)
from app.services.chat import get_chat_session

router = APIRouter(prefix="/agent", tags=["agent"])


def _get_agent_model(
    db: Session,
    user_id: int,
    model_name: str | None = None,
) -> AIModel:
    if model_name:
        model = db.scalar(
            select(AIModel).where(
                AIModel.name == model_name,
                AIModel.user_id == user_id,
            )
        )
    else:
        model = db.scalar(
            select(AIModel).where(
                AIModel.user_id == user_id,
                AIModel.is_active.is_(True),
            )
        )
    if model is None:
        raise AgentModelNotFound("模型未找到")
    if not model.is_active:
        raise AgentModelNotFound("该模型已停用")
    return model


@router.post("/runs")
async def agent_run(
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
    model_config = _get_agent_model(db, current_user.id, payload.model)

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


@router.post("/sessions/{session_id}/decisions")
async def decide_agent_operation(
    session_id: int,
    payload: AgentDecisionRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    ctx = agent_context(
        household_id=payload.household_id,
        session_id=session_id,
        db=db,
        current_user=current_user,
    )
    model_config = _get_agent_model(db, current_user.id)

    return StreamingResponse(
        resume_agent(
            context=ctx,
            decision=payload.model_dump(),
            model_config=model_config,
            db=db,
        ),
        media_type="text/event-stream",
    )


@router.get(
    "/sessions/{session_id}/pending",
    response_model=PendingApprovalRead | None,
)
async def get_pending_agent_operation(
    session_id: int,
    household_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    ctx = agent_context(
        household_id=household_id,
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

    saver = await get_checkpointer()
    checkpoint = await saver.aget_tuple(
        {
            "configurable": {
                "thread_id": agent_thread_id(ctx),
            }
        }
    )

    if checkpoint is None:
        return None

    pending = checkpoint.checkpoint.get("channel_values", {}).get("pending_approval")
    if not pending:
        return None

    return PendingApprovalRead.model_validate(pending)
