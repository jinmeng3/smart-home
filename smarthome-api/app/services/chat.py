import json
from collections.abc import Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AIModel
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatCompletionRequest


def get_current_ai_model(db: Session, current_user: User) -> AIModel:
    """获取当前用户绑定的 AI 模型。"""
    model = db.scalar(select(AIModel).where(AIModel.user_id == current_user.id))
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model


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


def list_user_chat_sessions(db: Session, current_user: User) -> list[ChatSession]:
    """列出当前用户的全部聊天会话。"""
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.updated_at.desc())
        ).all()
    )


def list_session_messages(
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


def save_request_messages(
    db: Session, session: ChatSession, payload: ChatCompletionRequest
) -> None:
    """保存本次请求中的消息。"""
    saved_messages = [
        ChatMessage(
            session_id=session.id,
            role=message.role,
            content=message.content,
        )
        for message in payload.messages
    ]
    db.add_all(saved_messages)
    db.commit()


def save_assistant_message(db: Session, session_id: int, content: str) -> None:
    """保存助手回复，空内容直接跳过。"""
    if not content.strip():
        return

    db.add(ChatMessage(session_id=session_id, role="assistant", content=content))
    db.commit()


def get_chat_completions_url(api_endpoint: str) -> str:
    """规范化上游 chat completions 地址。"""
    endpoint = api_endpoint.strip().rstrip("/")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    return f"{endpoint}/v1/chat/completions"


def build_chat_payload(model: AIModel, payload: ChatCompletionRequest) -> dict:
    chat_payload = {
        "model": model.name,
        "messages": [message.model_dump() for message in payload.messages],
        "stream": payload.stream,
        "temperature": model.temperature,
        "max_tokens": model.max_tokens,
    }

    return chat_payload


def build_chat_headers(model: AIModel) -> dict:
    return {
        "Authorization": f"Bearer {model.api_key.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "SmartHomeAPI/0.1",
    }


def build_chat_request(model: AIModel, payload: ChatCompletionRequest) -> Request:
    """构造上游请求对象。"""
    if not model.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Model is disabled"
        )

    if not model.api_endpoint or not model.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model endpoint or api key is missing",
        )

    return Request(
        get_chat_completions_url(model.api_endpoint),
        data=json.dumps(build_chat_payload(model, payload)).encode("utf-8"),
        headers=build_chat_headers(model),
        method="POST",
    )


def read_upstream_error(error: HTTPError) -> str:
    """读取并解析上游错误信息。"""
    raw_body = error.read().decode("utf-8", errors="ignore")
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body.strip() or error.reason

    detail = data.get("error", data)
    if isinstance(detail, dict):
        return detail.get("message") or json.dumps(detail, ensure_ascii=False)
    return str(detail)


def parse_stream_delta(chunk: bytes) -> str:
    """从流式 chunk 中提取增量内容。"""
    content = ""
    for line in chunk.decode("utf-8", errors="ignore").splitlines():
        if not line.startswith("data: "):
            continue

        data = line[6:].strip()
        if not data or data == "[DONE]":
            continue

        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue

        content += payload.get("choices", [{}])[0].get("delta", {}).get("content") or ""
    return content


def stream_chat_response(
    request: Request, db: Session | None = None, session_id: int | None = None
) -> Iterator[bytes]:
    """流式转发上游响应，并在结束后保存助手消息。"""
    assistant_chunks = []

    try:
        with urlopen(request, timeout=60) as response:
            while True:
                chunk = response.read(4096)
                if not chunk:
                    break

                assistant_chunks.append(parse_stream_delta(chunk))
                yield chunk
    except HTTPError as exc:
        yield f"data: {json.dumps({'error': read_upstream_error(exc)}, ensure_ascii=False)}\n\n".encode()
    except URLError as exc:
        yield f"data: {json.dumps({'error': str(exc.reason)}, ensure_ascii=False)}\n\n".encode()
    finally:
        if db is not None and session_id is not None:
            save_assistant_message(db, session_id, "".join(assistant_chunks))


def create_chat_completion(request: Request) -> dict:
    """发起非流式聊天请求并返回解析结果。"""
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(
            status_code=exc.code, detail=read_upstream_error(exc)
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc.reason)
        ) from exc


def extract_assistant_content(response_data: dict) -> str:
    """提取非流式响应里的助手内容。"""
    return response_data.get("choices", [{}])[0].get("message", {}).get("content") or ""
