from enum import IntEnum
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse[T](BaseModel):
    code: int = 0
    message: str = "ok"
    data: T | None = None

    def model_dump(self, **kwargs):
        """默认使用别名序列化，确保 camelCase 字段名正确输出。"""
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)

    @classmethod
    def ok(cls, data: T | None = None, message: str = "ok") -> "ApiResponse[T]":
        return cls(code=AppCode.SUCCESS, message=message, data=data)

    @classmethod
    def fail(cls, code: int, message: str, data: T | None = None) -> "ApiResponse[T]":
        return cls(code=code, message=message, data=data)


class AppCode(IntEnum):
    SUCCESS = 0
    BAD_REQUEST = 40000
    UNAUTHORIZED = 40100
    FORBIDDEN = 40300
    NOT_FOUND = 40400
    CONFLICT = 40900
    LOCKED = 42300
    TOO_MANY_REQUESTS = 42900
    PAYLOAD_TOO_LARGE = 41300
    UNSUPPORTED_MEDIA_TYPE = 41500
    UNPROCESSABLE_ENTITY = 42200
    INTERNAL_SERVER_ERROR = 50000
    BAD_GATEWAY = 50200
