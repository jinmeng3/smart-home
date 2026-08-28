import time
from collections import defaultdict, deque
from threading import Lock

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.errors import AgentBudgetExceededError, AgentRateLimitError
from app.core.config import get_settings
from app.models.agent_usage import AgentUsageDaily
from app.utils.time import today_utc

_rate_limit_buckets: dict[int, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def check_rate_limit(user_id: int) -> None:
    """检查用户是否超过每分钟请求限制。"""
    settings = get_settings()
    if settings.development_mode and not settings.production_mode:
        return

    now = time.monotonic()
    window = 60.0
    with _rate_limit_lock:
        bucket = _rate_limit_buckets[user_id]

        while bucket and bucket[0] < now - window:
            bucket.popleft()

        if len(bucket) >= settings.agent_rate_limit_per_minute:
            raise AgentRateLimitError(
                f"请求过于频繁，每分钟最多 {settings.agent_rate_limit_per_minute} 次"
            )

        bucket.append(now)


def check_daily_budget(db: Session, user_id: int) -> None:
    """检查用户今日 token 预算是否已超限。"""
    settings = get_settings()
    if settings.agent_daily_budget_tokens <= 0:
        return

    today = today_utc().strftime("%Y-%m-%d")
    result = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    AgentUsageDaily.total_input_tokens
                    + AgentUsageDaily.total_output_tokens
                ),
                0,
            )
        ).where(
            AgentUsageDaily.user_id == user_id,
            AgentUsageDaily.date == today,
        )
    )
    if result is not None and result >= settings.agent_daily_budget_tokens:
        raise AgentBudgetExceededError(
            f"今日 token 预算已超限（{result}/{settings.agent_daily_budget_tokens}）"
        )
