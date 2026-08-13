import json
import re
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import HTTPException, status
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_model_cache
from app.models.ai import AIModel
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatCompletionRequest

# === 聊天会话 ===


def get_chat_session(
    db: Session, current_user: User, session_id: int | None, messages: list
) -> ChatSession:
    """获取或创建聊天会话。"""
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
        return session

    title = next(
        (
            message.content.strip()[:120]
            for message in messages
            if message.role == "user"
        ),
        "新对话",
    )
    session = ChatSession(user_id=current_user.id, title=title or "新对话")
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
    db: Session, current_user: User, session_id: int
) -> list[ChatMessage]:
    """列出指定会话下的消息。"""
    get_chat_session(db, current_user, session_id, [])
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        ).all()
    )


def delete_chat_session_service(
    db: Session, current_user: User, session_id: int
) -> None:
    """删除指定聊天会话及其所有消息。"""
    session = get_chat_session(db, current_user, session_id, [])
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()


# === SSE 格式化 ===


def format_stream_error(error: str) -> bytes:
    return f"data: {json.dumps({'error': error}, ensure_ascii=False)}\n\n".encode()


def format_stream_content(content: str) -> bytes:
    payload = {"choices": [{"delta": {"content": content}}]}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def format_stream_done() -> bytes:
    return b"data: [DONE]\n\n"


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

    # 用户消息
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
        input={"messages": [HumanMessage(content=payload.messages[-1].content)]},
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
) -> Generator[bytes, None, None]:
    model_config = db.scalar(select(AIModel).where(AIModel.name == payload.model))
    if model_config is None:
        yield format_stream_error("Model not found")
        return
    session = get_chat_session(db, current_user, payload.session_id, payload.messages)

    # 先提交用户消息，避免异常时丢失
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
            input={"messages": [HumanMessage(content=payload.messages[-1].content)]},
            config=config,
            stream_mode="messages",
        ):
            if hasattr(msg_chunk, "content") and msg_chunk.content:
                chunk_text = str(msg_chunk.content)
                collected += chunk_text
                yield format_stream_content(chunk_text)

    except Exception as e:  # noqa: BLE001
        yield format_stream_error(str(e))
        return

    content = re.sub(r"<think>.*?</think>", "", collected, flags=re.DOTALL).strip()
    if content.strip():
        db.add(ChatMessage(session_id=session.id, content=content, role="assistant"))
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
