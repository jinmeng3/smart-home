"""会话树存储的 SQLAlchemy 模型。

采用「append-only 变更日志」建模，与文档的 JSONL v4 持久化语义一致：

- ``session_tree_sessions``：会话元信息（目录）。
- ``session_tree_mutations``：每条 mutation 一行，按 ``seq`` 有序；加载时
  逐条重放到 ``SessionState`` 重建内存状态。

SQLite 事务 + WAL 提供原子性（等价于 JSONL 的 torn-tail 修复：要么整条
mutation 生效，要么不生效）。
"""

from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SessionTreeSession(Base):
    __tablename__ = "session_tree_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_session_tree_sessions_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Unix ms"
    )


class SessionTreeMutation(Base):
    __tablename__ = "session_tree_mutations"
    __table_args__ = (
        Index("ix_session_tree_mutations_session_seq", "session_id", "seq"),
        UniqueConstraint("session_id", "seq", name="uq_session_tree_mutations_session_seq"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("session_tree_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False, comment="全局递增序列号")
    kind: Mapped[str] = mapped_column(String(16), nullable=False, comment="entry/record/lane/fact")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, comment="完整 mutation JSON")
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Unix ms")
