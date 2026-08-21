"""聊天流式响应的 SSE 格式化工具。"""

import json


def format_stream_error(error: str) -> bytes:
    return f"data: {json.dumps({'error': error}, ensure_ascii=False)}\n\n".encode()


def format_stream_content(content: str) -> bytes:
    payload = {"choices": [{"delta": {"content": content}}]}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


def format_stream_done() -> bytes:
    return b"data: [DONE]\n\n"


def format_stream_message_id(message_id: int) -> bytes:
    return f"data: {json.dumps({'message_id': message_id}, ensure_ascii=False)}\n\n".encode()
