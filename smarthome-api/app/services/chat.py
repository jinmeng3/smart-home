import re
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import HTTPException, status
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_model_cache
from app.models.ai import AIModel
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatCompletionRequest
from app.services.chat_sse import (
    format_stream_content,
    format_stream_error,
    format_stream_message_id,
)

# === 聊天会话 ===


def get_chat_session(
    db: Session,
    current_user: User,
    session_id: int | None,
    messages: list,
    *,
    household_id: int | None = None,
    mode: str = "agent",
    model_name: str | None = None,
) -> ChatSession:
    """获取或创建聊天会话，必要时绑定/校验家庭归属。"""
    if session_id is not None:
        session = db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
                               
        if household_id is not None:
            if session.household_id is not None and session.household_id != household_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="会话不属于该家庭",
                )
            if session.household_id is None:
                session.household_id = household_id
                db.flush()
        return session

    title = next(
        (
            message.content.strip()[:120]
            for message in messages
            if message.role == "user"
        ),
        "新对话",
    )
    session = ChatSession(
        user_id=current_user.id,
        title=title or "新对话",
        household_id=household_id,
        mode=mode,
        model_name=model_name,
    )
    db.add(session)
    db.flush()
    return session


def list_chat_sessions_service(db: Session, current_user: User) -> list[ChatSession]:
    """列出当前用户的全部聊天会话。"""
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.updated_at.desc())
        ).all()
    )


def list_chat_messages_service(
    db: Session,
    current_user: User,
    session_id: int,
    page: int = 1,
    page_size: int = 50,
) -> list[ChatMessage]:
    """列出指定会话下的消息，支持分页（按时间倒序取最新消息）。"""
    get_chat_session(db, current_user, session_id, [])
    offset = max(0, (page - 1) * page_size)
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).all()
    )[::-1]


def delete_chat_session_service(
    db: Session, current_user: User, session_id: int
) -> None:
    """删除指定聊天会话及其所有消息。"""
    session = get_chat_session(db, current_user, session_id, [])
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()


# === 对话补全 ===


def _to_langchain_messages(messages: list) -> list:
    """把 ChatCompletionMessage 列表转换为 LangChain 消息列表（纯对话模式不涉及工具消息）。"""
    result = []
    for message in messages:
        role = message.role
        if role == "system":
            result.append(SystemMessage(content=message.content))
        elif role == "user":
            result.append(HumanMessage(content=message.content))
        elif role == "assistant":
            result.append(AIMessage(content=message.content))
    return result


# === 对话补全 ===


def create_chat_service(
    payload: ChatCompletionRequest,
    current_user: User,
    db: Session,
) -> str:
    model_config = db.scalar(select(AIModel).where(AIModel.name == payload.model))
    if model_config is None:
        raise HTTPException(status_code=404, detail="Model not found")
    session = get_chat_session(db, current_user, payload.session_id, payload.messages)

          
    user_message = ChatMessage(
        session_id=session.id,
        content=payload.messages[-1].content,
        role=payload.messages[-1].role,
    )
    db.add(user_message)

    model_cache = get_model_cache()
    model = model_cache.get(model_config)
    agent = create_agent(model=model)
    config: RunnableConfig = {"configurable": {"thread_id": str(session.id)}}

    result = agent.invoke(
        input={"messages": _to_langchain_messages(payload.messages)},
        config=config,
    )
    content = result["messages"][-1].content

    db.add(ChatMessage(session_id=session.id, content=content, role="assistant"))
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    return content


def create_chat_service_stream(
    payload: ChatCompletionRequest,
    current_user: User,
    db: Session,
    *,
    persist_user_message: bool = True,
) -> Generator[bytes, None, None]:
    model_config = db.scalar(select(AIModel).where(AIModel.name == payload.model))
    if model_config is None:
        yield format_stream_error("Model not found")
        return
    session = get_chat_session(db, current_user, payload.session_id, payload.messages)

    if persist_user_message:
        db.add(
            ChatMessage(
                session_id=session.id,
                content=payload.messages[-1].content,
                role=payload.messages[-1].role,
            )
        )
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

    model_cache = get_model_cache()
    model = model_cache.get(model_config)
    agent = create_agent(model=model)
    config: RunnableConfig = {"configurable": {"thread_id": str(session.id)}}

    collected = ""
    try:
        for msg_chunk, _metadata in agent.stream(
            input={"messages": _to_langchain_messages(payload.messages)},
            config=config,
            stream_mode="messages",
        ):
            if hasattr(msg_chunk, "content") and msg_chunk.content:
                chunk_text = str(msg_chunk.content)
                collected += chunk_text
                yield format_stream_content(chunk_text)

    except Exception as e:  # noqa: BLE001  # 将任意流式异常转为 SSE 错误响应，避免连接中断
        yield format_stream_error(str(e))
        return

    content = re.sub(r"<think>.*?</think>", "", collected, flags=re.DOTALL).strip()
    if content.strip():
        assistant_message = ChatMessage(
            session_id=session.id, content=content, role="assistant"
        )
        db.add(assistant_message)
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        yield format_stream_message_id(assistant_message.id)


def prepare_regenerate(
    db: Session,
    current_user: User,
    session_id: int,
    target_message_id: int,
) -> tuple[ChatMessage, list[ChatMessage]]:
    """准备重新生成：定位目标助手回复与其前最近的用户消息，删除旧回复并返回历史。

    覆盖策略：删除目标助手消息及其之后的所有消息，用旧用户消息重新生成，
    从而避免重复保存用户消息、也不会留下旧回答的多个版本。
    """
    session = get_chat_session(db, current_user, session_id, [])

    target = db.get(ChatMessage, target_message_id)
    if target is None or target.session_id != session.id or target.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标消息不存在或不是助手回复",
        )

    user_message = db.scalar(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session.id,
            ChatMessage.id < target_message_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.id.desc())
        .limit(1)
    )
    if user_message is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="找不到对应的用户消息，无法重新生成",
        )

    db.execute(
        delete(ChatMessage).where(
            ChatMessage.session_id == session.id,
            ChatMessage.id >= target_message_id,
        )
    )

    history_rows = list(
        db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session.id,
                ChatMessage.id < user_message.id,
            )
            .order_by(ChatMessage.id.asc())
        ).all()
    )

    return user_message, history_rows
