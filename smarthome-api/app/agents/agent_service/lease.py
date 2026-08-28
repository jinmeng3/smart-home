import logging
from datetime import UTC, datetime, timedelta
from app.utils.time import now_utc

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent_lease import AgentRunLease

logger = logging.getLogger(__name__)


def acquire_run_lease(
    db: Session,
    *,
    user_id: int,
    household_id: int,
    session_id: int,
    run_id: str,
    thread_id: str,
) -> bool:
    """尝试获取会话运行租约。

    - 已持有有效租约（未超时）→ 返回 False（409，避免并发写入同一 thread_id）。
    - 无租约或租约超时 → 删除旧租约并写入新租约，返回 True。
    """
    lease = db.scalar(
        select(AgentRunLease).where(
            AgentRunLease.user_id == user_id,
            AgentRunLease.household_id == household_id,
            AgentRunLease.session_id == session_id,
        )
    )
    ttl_seconds = get_settings().agent_lease_ttl_seconds
    now = now_utc()
    if lease is not None:
        created = lease.created_at
        if created is not None:
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if now - created < timedelta(seconds=ttl_seconds):
                return False
        # 租约超时：接管前先清理旧记录
        db.execute(delete(AgentRunLease).where(AgentRunLease.id == lease.id))
        try:
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            return False

    db.add(
        AgentRunLease(
            user_id=user_id,
            household_id=household_id,
            session_id=session_id,
            run_id=run_id,
            thread_id=thread_id,
        )
    )
    try:
        db.commit()
        return True
    except IntegrityError:
        # 并发竞争：另一个请求已写入租约
        db.rollback()
        return False
    except Exception:  # noqa: BLE001
        db.rollback()
        return False


def release_run_lease(
    db: Session,
    *,
    user_id: int,
    household_id: int,
    session_id: int,
) -> None:
    """释放会话运行租约（幂等，失败仅记录日志不影响主流程）。"""
    try:
        db.execute(
            delete(AgentRunLease).where(
                AgentRunLease.user_id == user_id,
                AgentRunLease.household_id == household_id,
                AgentRunLease.session_id == session_id,
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001  # 释放失败不应中断主流程
        db.rollback()


def is_session_running(
    db: Session, *, user_id: int, household_id: int, session_id: int
) -> bool:
    """查询会话当前是否持有有效（未超时）租约。"""
    lease = db.scalar(
        select(AgentRunLease).where(
            AgentRunLease.user_id == user_id,
            AgentRunLease.household_id == household_id,
            AgentRunLease.session_id == session_id,
        )
    )
    if lease is None:
        return False
    created = lease.created_at
    if created is None:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    ttl_seconds = get_settings().agent_lease_ttl_seconds
    return now_utc() - created < timedelta(seconds=ttl_seconds)
