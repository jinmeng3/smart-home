"""待审批操作（pending approval）过期、取消与清理管理。

§5.2：增加待审批过期、取消和清理机制。

- ``make_pending`` 创建 pending 时写入 created_at / expires_at。
- ``is_pending_expired`` 判断 pending 是否已过期。
- ``cancel_pending_approval`` 取消待审批操作（记录审计 + 清理 checkpoint 线程）。
"""

import logging
from datetime import datetime, timezone

from app.agents.context import AgentContext
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def make_pending(state: dict) -> dict:
    """在创建 pending_approval dict 后注入 created_at / expires_at。

    约定：由 ``risk_node`` 在构建 pending dict 后调用此函数完成设置。
    """
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    ttl = get_settings().approval_ttl_seconds
    expires_at_timestamp = now.timestamp() + ttl
    state["created_at"] = created_at
    state["expires_at"] = expires_at_timestamp
    return state


def is_pending_expired(pending: dict | None) -> bool:
    """判断 pending 是否已过期。

    向后兼容：缺 expires_at 时视为未过期（旧 checkpoint 仍可审批）。
    """
    if pending is None:
        return True
    expires_at = pending.get("expires_at")
    if expires_at is None:
        return False  # 旧记录，向后兼容
    now = datetime.now(timezone.utc).timestamp()
    return now > float(expires_at)


async def cancel_pending_approval(
    saver,
    thread_id: str,
    *,
    context: AgentContext,
    pending: dict,
) -> None:
    """取消待审批操作：记录审计、删除 checkpoint 线程以清理 pending 状态。

    注意：``saver.adelete_thread`` 会删除整个 checkpoint 线程，
    包括消息历史；但由于 Agent 消息历史由会话树管理（压缩），
    下一次 ``run_agent`` 会从会话树重建并自动 ``adelete_thread``，
    因此删除线程不会丢失数据。"""
    from app.agents.audit.recorder import get_audit_recorder

    now = datetime.now(timezone.utc)
    audit = get_audit_recorder()
    run_id = pending.get("run_id", "")

    # 1. 记录取消决定到审计
    audit.record_approval_decision(
        run_id=run_id,
        approval_id=pending.get("approval_id", ""),
        decision="cancelled",
        automatic=False,
    )

    # 2. 记录 run 结束（取消状态）
    audit.record_run_end(
        run_id,
        status="cancelled",
        message=f"用户于 {now.isoformat()} 主动取消了待审批操作",
    )

    # 3. 删除 checkpoint 线程，清理 pending 状态
    try:
        await saver.adelete_thread(thread_id)
    except Exception:  # 清理失败不应中断主流程
        logger.warning("取消待审批时清理 checkpoint 线程失败", exc_info=True)
