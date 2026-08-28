"""时间相关工具函数。

集中提供统一的时间取法，避免业务代码里散落 ``datetime.now(timezone.utc)`` /
``datetime.now(UTC)`` 两种不一致写法，也便于后续统一时区策略。
"""
from datetime import UTC, date, datetime
from time import time


def now_utc() -> datetime:
    """当前 UTC 时间（带时区）。"""
    return datetime.now(UTC)


def today_utc() -> date:
    """当前 UTC 日期。"""
    return datetime.now(UTC).date()


def start_of_today_utc() -> datetime:
    """当前 UTC 当天 00:00:00（带时区）。"""
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def now_timestamp() -> float:
    """当前 Unix 时间戳（秒，浮点）。"""
    return time()


def now_utc_ms() -> int:
    """当前 Unix 时间戳（毫秒，整型）。"""
    return int(time() * 1000)
