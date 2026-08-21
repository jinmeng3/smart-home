from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.user import User
from app.schemas.chat import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatMessageRead,
    ChatSessionRead,
    RegenerateRequest,
    SessionModelUpdate,
    SessionModeUpdate,
)
from app.schemas.common import ApiResponse
from app.services.chat import (
    create_chat_service,
    create_chat_service_stream,
    delete_chat_session_service,
    get_chat_session,
    list_chat_messages_service,
    list_chat_sessions_service,
    prepare_regenerate,
)

router = APIRouter(prefix="/chat", tags=["chat"])


# === 聊天会话 ===


@router.get("/sessions", response_model=ApiResponse[list[ChatSessionRead]])
def list_chat_sessions(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[ChatSessionRead]]:
    """按更新时间列出当前用户的聊天会话。"""
    return ApiResponse(data=list_chat_sessions_service(db, current_user))


@router.post(
    "/sessions",
    response_model=ApiResponse[ChatSessionRead],
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    mode: str = "agent",
    model_name: str | None = None,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[ChatSessionRead]:
    """创建一条空聊天会话，可指定会话模式与模型。"""
    session = get_chat_session(
        db, current_user, None, [], mode=mode, model_name=model_name
    )
    db.commit()
    db.refresh(session)
    return ApiResponse(data=session, message="created")


@router.patch(
    "/sessions/{session_id}/mode",
    response_model=ApiResponse[ChatSessionRead],
)
def update_session_mode(
    session_id: int,
    payload: SessionModeUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[ChatSessionRead]:
    """更新指定会话的模式。"""
    session = get_chat_session(db, current_user, session_id, [])
    session.mode = payload.mode
    db.commit()
    db.refresh(session)
    return ApiResponse(data=session, message="updated")


@router.patch(
    "/sessions/{session_id}/model",
    response_model=ApiResponse[ChatSessionRead],
)
def update_session_model(
    session_id: int,
    payload: SessionModelUpdate,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[ChatSessionRead]:
    """更新指定会话使用的模型名。"""
    session = get_chat_session(db, current_user, session_id, [])
    session.model_name = payload.model_name
    db.commit()
    db.refresh(session)
    return ApiResponse(data=session, message="updated")


# === 聊天消息 ===


@router.get(
    "/sessions/{session_id}/messages", response_model=ApiResponse[list[ChatMessageRead]]
)
def list_chat_messages(
    session_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[ChatMessageRead]]:
    """读取指定会话的历史消息，支持分页（按时间倒序取最新消息）。"""
    return ApiResponse(
        data=list_chat_messages_service(db, current_user, session_id, page, page_size)
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """删除指定聊天会话及其所有消息。"""
    delete_chat_session_service(db, current_user, session_id)


# === 对话补全 ===


@router.post("/completions")
def create_chat(
    payload: ChatCompletionRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """转发聊天请求，并根据 stream 参数返回普通或流式响应。"""
    if payload.stream:
        return StreamingResponse(
            create_chat_service_stream(payload, current_user, db),
            media_type="text/event-stream",
        )
    else:
        return ApiResponse.ok(data=create_chat_service(payload, current_user, db))


@router.post("/sessions/{session_id}/regenerate")
def regenerate_chat(
    session_id: int,
    payload: RegenerateRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """重新生成指定助手回复（对话模式：完全不绑定工具）。"""
    user_message, history_rows = prepare_regenerate(
        db, current_user, session_id, payload.target_message_id
    )
    db.commit()

    messages = [
        ChatCompletionMessage(
            role="assistant" if row.role == "assistant" else "user",
            content=row.content,
        )
        for row in history_rows
    ]
    messages.append(ChatCompletionMessage(role="user", content=user_message.content))

    chat_payload = ChatCompletionRequest(
        model=payload.model,
        messages=messages,
        session_id=session_id,
        stream=True,
    )
    return StreamingResponse(
        create_chat_service_stream(
            chat_payload, current_user, db, persist_user_message=False
        ),
        media_type="text/event-stream",
    )
