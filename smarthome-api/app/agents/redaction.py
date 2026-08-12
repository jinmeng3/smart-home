"""日志与事件脱敏：屏蔽 API Key、JWT、密钥，避免敏感信息泄漏到事件/日志/堆栈。"""

import logging
import re

# 常见敏感字段名：KEY / SECRET / TOKEN / PASSWORD / AUTHORIZATION
_SENSITIVE_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9_\-]{6,})"),  # OpenAI 风格
    re.compile(r"(Bearer\s+[A-Za-z0-9_\-\.=]{8,})", re.IGNORECASE),
    re.compile(r"(\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-\.]{8,})"),  # JWT
]
_MASK = "<redacted>"


def redact_text(text: str) -> str:
    """将文本中的密钥、令牌替换为占位符。"""
    if not text:
        return text
    for pattern in _SENSITIVE_PATTERNS:
        text = (
            pattern.sub(f"\\1⚠ {_MASK}", text)
            if "sk-" in pattern.pattern
            else pattern.sub(_MASK, text)
        )
    return text


def redact_fields(data: dict) -> dict:
    """递归屏蔽 dict 中 value 属于敏感字段名的值。"""
    if not isinstance(data, dict):
        return data
    sensitive_keys = {
        "api_key",
        "apiKey",
        "token",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "authorization",
    }
    return {
        k: (
            _MASK
            if k in sensitive_keys and isinstance(v, str)
            else redact_fields(v)
            if isinstance(v, dict)
            else v
        )
        for k, v in data.items()
    }


class RedactingFilter(logging.Filter):
    """日志过滤器：在记录输出前脱敏 message 与 args。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str) and "sk-" in record.msg.lower():
            record.msg = redact_text(record.msg)
        return True
