"""聊天流式响应的 SSE 格式化工具。"""

from app.utils.json import dump_json


def format_stream_error(error: str) -> bytes:
    return f"data: {dump_json({'error': error})}\n\n".encode()


def format_stream_content(content: str) -> bytes:
    payload = {"choices": [{"delta": {"content": content}}]}
    return f"data: {dump_json(payload)}\n\n".encode()


def format_stream_done() -> bytes:
    return b"data: [DONE]\n\n"


def format_stream_message_id(message_id: int) -> bytes:
    return f"data: {dump_json({'message_id': message_id})}\n\n".encode()
