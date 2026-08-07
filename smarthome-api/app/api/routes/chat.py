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
from app.services.ai_model import read_ai_model_service
from app.services.chat import (
    build_chat_request,
    create_chat_completion,
    extract_assistant_content,
    get_chat_session,
    list_chat_messages_service,
    list_chat_sessions_service,
    save_assistant_message,
    save_request_messages,
    stream_chat_response,
)

router = APIRouter(prefix="/chat", tags=["chat"])
codex_router = APIRouter(tags=["chat"])


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


# === 对话补全 ===


@codex_router.post("/v1/chat/completions")
@router.post("/completions")
def create_chat(
    payload: ChatCompletionRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    """转发聊天请求，并根据 stream 参数返回普通或流式响应。"""
    model = read_ai_model_service(db, current_user)
    session = get_chat_session(db, current_user, payload.session_id, payload.messages)
    save_request_messages(db, session, payload)
    request = build_chat_request(model, payload)

    if payload.stream:
        return StreamingResponse(
            stream_chat_response(request, db, session.id),
            media_type="text/event-stream",
        )

    response_data = create_chat_completion(request)
    save_assistant_message(db, session.id, extract_assistant_content(response_data))
    return response_data
