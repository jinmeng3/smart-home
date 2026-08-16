import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock

from app.agents.context import AgentContext
from app.agents.errors import AgentBudgetExceededError, AgentRateLimitError
from app.core.config import get_settings
from app.models.agent_usage import AgentUsage, AgentUsageDaily
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# 内存限流器：{user_id: [timestamp, ...]}
_rate_limit_buckets: dict[int, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def check_rate_limit(user_id: int) -> None:
    """检查用户是否超过每分钟请求限制。"""
    settings = get_settings()
    if settings.development_mode and not settings.production_mode:
        return  # 开发模式不限流

    now = time.monotonic()
    window = 60.0  # 1 分钟窗口
    with _rate_limit_lock:  # 滑动日志算法
        bucket = _rate_limit_buckets[user_id]
        # bucket[0] < now - windo 判断是否过了时间窗口，如果过了就重置起始点
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
        return  # 无限制

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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


def store_usage(
    db: Session,
    context: AgentContext,
    run_id: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    tool_call_count: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """存储 agent 使用统计到数据库。"""
    usage = db.scalar(select(AgentUsage).where(AgentUsage.run_id == run_id))
    is_new_run = usage is None
    if usage is None:
        usage = AgentUsage(
            user_id=context.user_id,
            household_id=context.household_id,
            run_id=run_id,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status=status,
            error_message=error_message,
        )
        db.add(usage)
    else:
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.tool_call_count += tool_call_count
        usage.status = status
        usage.error_message = error_message

    # 使用数据库 upsert 原子更新日汇总，避免多 worker 首次写入时产生重复行。
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dialect = db.get_bind().dialect.name
    values = {
        "user_id": context.user_id,
        "date": today,
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "run_count": 1 if is_new_run else 0,
    }
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert

        statement = insert(AgentUsageDaily).values(**values)
        statement = statement.on_conflict_do_update(
            constraint="uq_agent_usage_daily_user_date",
            set_={
                "total_input_tokens": AgentUsageDaily.total_input_tokens + input_tokens,
                "total_output_tokens": AgentUsageDaily.total_output_tokens
                + output_tokens,
                "run_count": AgentUsageDaily.run_count + (1 if is_new_run else 0),
                "updated_at": func.now(),
            },
        )
        db.execute(statement)
    else:
        daily = db.scalar(
            select(AgentUsageDaily).where(
                AgentUsageDaily.user_id == context.user_id,
                AgentUsageDaily.date == today,
            )
        )
        if daily is None:
            db.add(AgentUsageDaily(**values))
        else:
            daily.total_input_tokens += input_tokens
            daily.total_output_tokens += output_tokens
            daily.run_count += 1 if is_new_run else 0

    db.commit()
