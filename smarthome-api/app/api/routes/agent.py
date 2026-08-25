from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.agent_service.lease import is_session_running
from app.agents.agent_service.pending import (
    cancel_pending_approval,
    is_pending_expired,
)
from app.agents.agent_service.resumer import agent_thread_id, resume_agent
from app.agents.agent_service.runner import run_agent
from app.agents.checkpointer import get_checkpointer
from app.agents.context import agent_context
from app.agents.errors import AgentModelNotFound
from app.agents.usage import get_latest_run_status
from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.ai import AIModel
from app.models.household import Household
from app.models.user import User
from app.schemas.agent import (
    AgentDecisionRequest,
    AgentRunRequest,
    PendingApprovalRead,
)
from app.schemas.chat import RegenerateRequest
from app.services.chat import get_chat_session, prepare_regenerate

router = APIRouter(prefix="/agent", tags=["agent"])


def _get_agent_model(
    db: Session,
    user_id: int,
    model_name: str | None = None,
    model_id: int | None = None,
) -> AIModel:
    """按模型 ID、模型名或当前激活模型解析用户的 AI 模型配置。

    优先级：model_id > model_name > 当前激活模型。
    使用模型 ID 定位可以避免可重名的模型名称带来的歧义（§4.3）。
    """
    if model_id is not None:
        model = db.scalar(
            select(AIModel).where(
                AIModel.id == model_id,
                AIModel.user_id == user_id,
            )
        )
    elif model_name:
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


def _extract_history_before_user(messages: list, target_content: str) -> list:
    """从 graph state 消息列表截取目标用户消息之前的完整历史（含工具中间状态）。"""
    result = []
    for message in messages:
        if isinstance(message, HumanMessage) and message.content == target_content:
            break
        if isinstance(message, SystemMessage):
            continue
        result.append(message)
    return result


@router.post("/runs")
async def agent_run(
    payload: AgentRunRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """创建一次 Agent 运行：校验上下文、检查待确认操作并以 SSE 流式返回。"""
    ctx = agent_context(
        household_id=payload.household_id,
        session_id=payload.session_id,
        db=db,
        current_user=current_user,
        tools_enabled=payload.tools_enabled,
    )

    get_chat_session(
        db=db,
        current_user=current_user,
        session_id=payload.session_id,
        messages=[],
        household_id=payload.household_id,
    )

    # 检查会话是否正在运行（§4.4）
    if is_session_running(
        db,
        user_id=current_user.id,
        household_id=payload.household_id,
        session_id=payload.session_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该会话正在运行中，请等待当前操作完成后再试",
        )

    saver = await get_checkpointer()
    checkpoint = await saver.aget_tuple(
        {"configurable": {"thread_id": agent_thread_id(ctx)}}
    )
    pending = (
        checkpoint.checkpoint.get("channel_values", {}).get("pending_approval")
        if checkpoint is not None
        else None
    )
    if pending and is_pending_expired(pending):
        # 过期的 pending 视为已清理，不阻塞新请求（§5.2）
        pending = None
    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="当前会话存在待确认操作，请先处理后再发起新请求",
        )

    model_config = _get_agent_model(db, current_user.id, payload.model)
    household = db.get(Household, payload.household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在")

    return StreamingResponse(
        run_agent(
            context=ctx,
            household_name=household.name,
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
    """提交待确认操作的批准/拒绝决定，并以发起 run 时的原模型恢复执行。"""
    ctx = agent_context(
        household_id=payload.household_id,
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

    # 检查会话是否正在运行（§4.4）
    if is_session_running(
        db,
        user_id=current_user.id,
        household_id=payload.household_id,
        session_id=session_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该会话正在运行中，请等待当前操作完成后再试",
        )

    saver = await get_checkpointer()
    checkpoint = await saver.aget_tuple(
        {"configurable": {"thread_id": agent_thread_id(ctx)}}
    )
    pending = (
        checkpoint.checkpoint.get("channel_values", {}).get("pending_approval")
        if checkpoint is not None
        else None
    )
    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="当前会话在该家庭下没有待确认操作",
        )
    if is_pending_expired(pending):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="待审批操作已过期，请重新发起操作并确认",
        )
    if pending["approval_id"] != payload.approval_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="确认请求已失效或不属于当前操作",
        )

    # 待确认 run 必须继续使用发起时的原模型，而非用户切换后的当前激活模型
    # 优先使用模型记录 ID（不可重名、不可变更），其次按模型名称定位（§4.3）
    model_id = pending.get("model_id")
    model_name = pending.get("model_name") or None
    model_config = _get_agent_model(
        db,
        current_user.id,
        model_name=model_name,
        model_id=int(model_id) if isinstance(model_id, int) else None,
    )

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
    """查询会话在当前家庭下是否存在待确认操作。"""
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
    if is_pending_expired(pending):
        return None

    return PendingApprovalRead.model_validate(pending)


@router.post("/sessions/{session_id}/cancel-pending")
async def cancel_pending_agent_operation(
    session_id: int,
    household_id: int,
    approval_id: str,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """取消当前会话的待审批操作（记录审计并清理 checkpoint 状态，§5.2）。"""
    ctx = agent_context(
        household_id=household_id,
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

    saver = await get_checkpointer()
    thread_id = agent_thread_id(ctx)
    checkpoint = await saver.aget_tuple({"configurable": {"thread_id": thread_id}})
    pending = (
        checkpoint.checkpoint.get("channel_values", {}).get("pending_approval")
        if checkpoint is not None
        else None
    )
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="当前会话在该家庭下没有待确认操作",
        )
    if pending["approval_id"] != approval_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="确认请求已失效或不属于当前操作",
        )

    await cancel_pending_approval(
        saver,
        thread_id,
        context=ctx,
        pending=pending,
    )
    return {"status": "cancelled"}


@router.post("/sessions/{session_id}/regenerate")
async def regenerate_agent(
    session_id: int,
    payload: RegenerateRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """重新生成指定助手回复（Agent 模式：回退 checkpoint 后重新运行，不重放写操作）。"""
    if payload.household_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent 重新生成需要 household_id",
        )

    ctx = agent_context(
        household_id=payload.household_id,
        session_id=session_id,
        db=db,
        current_user=current_user,
        tools_enabled=True,
    )

    saver = await get_checkpointer()
    checkpoint = await saver.aget_tuple(
        {"configurable": {"thread_id": agent_thread_id(ctx)}}
    )
    pending = (
        checkpoint.checkpoint.get("channel_values", {}).get("pending_approval")
        if checkpoint is not None
        else None
    )
    if pending and is_pending_expired(pending):
        pending = None
    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="当前会话存在待确认操作，请先处理后再重新生成",
        )

    user_message, _history_rows = prepare_regenerate(
        db, current_user, session_id, payload.target_message_id
    )
    db.commit()

    checkpoint_messages = (
        checkpoint.checkpoint.get("channel_values", {}).get("messages", [])
        if checkpoint is not None
        else []
    )
    history_messages = _extract_history_before_user(
        checkpoint_messages, user_message.content
    )

    await saver.adelete_thread(agent_thread_id(ctx))

    model_config = _get_agent_model(db, current_user.id, payload.model)
    household = db.get(Household, payload.household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="家庭不存在")

    return StreamingResponse(
        run_agent(
            context=ctx,
            household_name=household.name,
            message=user_message.content,
            model_config=model_config,
            db=db,
            history_messages=history_messages,
            persist_user_message=False,
        ),
        media_type="text/event-stream",
    )


@router.get("/sessions/{session_id}/run-status")
async def get_agent_run_status(
    session_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """查询会话最近一次 run 的状态与阶段，用于刷新或切换回会话时恢复状态。"""
    get_chat_session(db, current_user, session_id, [])
    result = get_latest_run_status(db, current_user.id, session_id)
    if result is None:
        return {"status": None, "phase": None}
    status_value, phase = result
    return {"status": status_value, "phase": phase}
