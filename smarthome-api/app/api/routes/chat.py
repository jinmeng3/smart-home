from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.user import User
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatMessageRead,
    ChatSessionRead,
)
from app.schemas.common import ApiResponse
from app.services.chat import (
    create_chat_service,
    create_chat_service_stream,
    delete_chat_session_service,
    get_chat_session,
    list_chat_messages_service,
    list_chat_sessions_service,
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
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[ChatSessionRead]:
    """创建一条空聊天会话。"""
    session = get_chat_session(db, current_user, None, [])
    db.commit()
    db.refresh(session)
    return ApiResponse(data=session, message="created")


# === 聊天消息 ===


@router.get(
    "/sessions/{session_id}/messages", response_model=ApiResponse[list[ChatMessageRead]]
)
def list_chat_messages(
    session_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[ChatMessageRead]]:
    """读取指定会话的历史消息。"""
    return ApiResponse(data=list_chat_messages_service(db, current_user, session_id))


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
