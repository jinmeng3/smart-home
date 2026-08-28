from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.context import AgentContext
from app.models.agent_usage import AgentUsage, AgentUsageDaily
from app.utils.time import today_utc


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
    phase: str | None = None,
    domain: str | None = None,
) -> None:
    """存储 agent 使用统计到数据库。"""
    usage = db.scalar(select(AgentUsage).where(AgentUsage.run_id == run_id))
    is_new_run = usage is None
    if usage is None:
        usage = AgentUsage(
            user_id=context.user_id,
            household_id=context.household_id,
            session_id=context.session_id,
            run_id=run_id,
            model_name=model_name,
            domain=domain,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status=status,
            phase=phase or "thinking",
            error_message=error_message,
        )
        db.add(usage)
    else:
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.tool_call_count += tool_call_count
        usage.status = status
        if domain is not None:
            usage.domain = domain
        if phase is not None:
            usage.phase = phase
        usage.error_message = error_message

    today = today_utc().strftime("%Y-%m-%d")
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


def start_run(
    db: Session,
    context: AgentContext,
    run_id: str,
    model_name: str,
    domain: str | None = None,
) -> None:
    """记录一次 run 的开始状态（running）。"""
    usage = db.scalar(select(AgentUsage).where(AgentUsage.run_id == run_id))
    if usage is not None:
        return
    db.add(
        AgentUsage(
            user_id=context.user_id,
            household_id=context.household_id,
            session_id=context.session_id,
            run_id=run_id,
            model_name=model_name,
            domain=domain,
            input_tokens=0,
            output_tokens=0,
            tool_call_count=0,
            status="running",
            phase="thinking",
        )
    )
    db.commit()


def update_run_phase(db: Session, run_id: str, phase: str) -> None:
    """更新 run 的阶段（thinking / executing / submitted）。"""
    usage = db.scalar(select(AgentUsage).where(AgentUsage.run_id == run_id))
    if usage is not None:
        usage.phase = phase
        db.commit()


def get_latest_run_status(
    db: Session,
    user_id: int,
    session_id: int,
) -> tuple[str, str] | None:
    """查询会话最近一次 run 的状态与阶段，按创建时间倒序取最新一条。"""
    usage = db.scalar(
        select(AgentUsage)
        .where(
            AgentUsage.user_id == user_id,
            AgentUsage.session_id == session_id,
        )
        .order_by(AgentUsage.id.desc())
        .limit(1)
    )
    if usage is None:
        return None
    return usage.status, usage.phase
