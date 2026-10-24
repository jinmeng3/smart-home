"""Agent 会话租约与待审批过期管理测试（§4.4、§5.2）。"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.agents.agent_service.lease import (
    get_run_lease as acquire_run_lease,
)
from app.agents.agent_service.lease import (
    is_session_running,
    release_run_lease,
)
from app.agents.agent_service.pending import is_pending_expired, make_pending
from app.db.base import Base
from app.models.agent_lease import AgentRunLease


@pytest.fixture
def db_session():
    """内存 SQLite 数据库会话。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ── 会话租约测试（§4.4）──


class TestAcquireRunLease:
    def test_acquire_new_lease(self, db_session: Session):
        """首次获取租约应成功。"""
        result = acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="thread-1",
        )
        assert result is True
        lease = db_session.scalars(
            select(AgentRunLease).where(AgentRunLease.session_id == 1)
        ).first()
        assert lease is not None
        assert lease.user_id == 1
        assert lease.run_id == "run-1"

    def test_acquire_conflict(self, db_session: Session):
        """同一会话冲突时返回 False。"""
        acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="thread-1",
        )
        result = acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-2",
            thread_id="thread-2",
        )
        assert result is False

    def test_acquire_different_session_allowed(self, db_session: Session):
        """不同会话互不干扰。"""
        assert acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="t-1",
        )
        assert acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=2,
            run_id="run-2",
            thread_id="t-2",
        )

    @patch("app.agents.agent_service.lease.get_settings")
    def test_takeover_stale_lease(self, mock_settings, db_session: Session):
        """超时租约可被接管。"""
        settings = MagicMock()
        settings.agent_lease_ttl_seconds = 120
        mock_settings.return_value = settings

        # 创建旧租约
        acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="t-1",
        )

        # 手动将租约创建时间设为 5 分钟前（超时）
        lease = db_session.scalars(
            select(AgentRunLease).where(AgentRunLease.session_id == 1)
        ).first()
        assert lease is not None, "租约应在创建后存在"
        old_time = datetime.now(UTC) - timedelta(seconds=300)
        lease.created_at = old_time
        db_session.commit()

        # 新租约应能接管
        result = acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-2",
            thread_id="t-2",
        )
        assert result is True
        updated = db_session.scalars(
            select(AgentRunLease).where(AgentRunLease.session_id == 1)
        ).first()
        assert updated is not None, "接管后应存在新租约"
        assert updated.run_id == "run-2"


class TestReleaseRunLease:
    def test_release(self, db_session: Session):
        """释放租约后会话不再处于运行状态。"""
        acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="t-1",
        )
        release_run_lease(db_session, user_id=1, household_id=1, session_id=1)
        assert (
            is_session_running(db_session, user_id=1, household_id=1, session_id=1)
            is False
        )

    def test_release_idempotent(self, db_session: Session):
        """释放不存在的租约不报错。"""
        release_run_lease(db_session, user_id=1, household_id=1, session_id=999)
        # 无异常即通过


class TestIsSessionRunning:
    def test_running_session(self, db_session: Session):
        acquire_run_lease(
            db_session,
            user_id=1,
            household_id=1,
            session_id=1,
            run_id="run-1",
            thread_id="t-1",
        )
        assert (
            is_session_running(db_session, user_id=1, household_id=1, session_id=1)
            is True
        )

    def test_no_lease(self, db_session: Session):
        assert (
            is_session_running(db_session, user_id=1, household_id=1, session_id=1)
            is False
        )


# ── 待审批过期测试（§5.2）──


class TestMakePending:
    def test_injects_expiry(self):
        """make_pending 应注入 created_at 和 expires_at。"""
        pending = {"approval_id": "a1", "run_id": "r1"}
        result = make_pending(pending)
        assert "created_at" in result
        assert "expires_at" in result
        # expires_at 应为未来时间
        assert result["expires_at"] > datetime.now(UTC).timestamp()


class TestIsPendingExpired:
    def test_fresh_pending(self):
        """新创建的 pending 不应过期。"""
        pending = make_pending({"approval_id": "a1"})
        assert is_pending_expired(pending) is False

    def test_expired_pending(self):
        """手动设置过期时间到过去后应判为过期。"""
        expired_time = datetime.now(UTC).timestamp() - 100
        pending = {"expires_at": expired_time}
        assert is_pending_expired(pending) is True

    def test_expired_pending_with_approval_id(self):
        """过期 pending 需要带 approval_id 验证。"""
        pending = {"approval_id": "a1", "expires_at": 0}
        assert is_pending_expired(pending) is True

    def test_none_pending(self):
        """None 视为过期。"""
        assert is_pending_expired(None) is True

    def test_no_expiry_field_backward_compat(self):
        """缺 expires_at 的旧记录视为未过期（向后兼容）。"""
        assert is_pending_expired({"approval_id": "a1"}) is False
