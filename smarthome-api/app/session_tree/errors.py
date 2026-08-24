"""会话树存储的错误类型。

对应 TypeScript 参考实现中的 ``SessionError``：所有业务错误都带一个
稳定的 ``code``，调用方（存储层 / 上层服务）据此区分处理。
"""

from __future__ import annotations

from typing import Literal

SessionErrorCode = Literal[
    "not_found",
    "already_exists",
    "invalid_entry",
    "invalid_payload",
    "invalid_lane",
    "invalid_query",
    "invalid_fork_target",
    "storage",
]


class SessionError(Exception):
    """会话树存储的统一业务异常。"""

    def __init__(self, code: SessionErrorCode, message: str) -> None:
        super().__init__(message)
        self.code: SessionErrorCode = code
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover - 调试辅助
        return f"SessionError({self.code!r}, {self.message!r})"
