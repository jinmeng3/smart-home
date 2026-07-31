from fastapi import APIRouter
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
    build_chat_request,
    create_chat_completion,
    extract_assistant_content,
    get_chat_session,
    get_current_ai_model,
    list_session_messages,
    list_user_chat_sessions,
    save_assistant_message,
    save_request_messages,
    stream_chat_response,
)

router = APIRouter(prefix="/chat", tags=["chat"])
codex_router = APIRouter(tags=["chat"])


@router.get("/sessions", response_model=ApiResponse[list[ChatSessionRead]])
def list_chat_sessions(
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[ChatSessionRead]]:
    return ApiResponse(data=list_user_chat_sessions(db, current_user))


@router.get(
    "/sessions/{session_id}/messages", response_model=ApiResponse[list[ChatMessageRead]]
)
def list_chat_messages(
    session_id: int,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ApiResponse[list[ChatMessageRead]]:
    return ApiResponse(data=list_session_messages(db, current_user, session_id))


@codex_router.post("/v1/chat/completions")
@router.post("/completions")
def create_chat(
    payload: ChatCompletionRequest,
    current_user: User = CURRENT_USER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
):
    model = get_current_ai_model(db, current_user)
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
