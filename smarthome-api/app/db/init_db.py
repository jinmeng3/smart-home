from sqlalchemy import inspect, text

import app.models  # noqa: F401  # 注册全部 ORM 模型，确保 create_all 能创建会话树等表
from app.db.base import Base
from app.db.session import engine


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def _ensure_columns() -> None:
    """对已有库补齐新增列（create_all 不会为已存在的表添加列）。"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "chat_sessions" in table_names:
        columns = {column["name"] for column in inspector.get_columns("chat_sessions")}
        if "mode" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE chat_sessions ADD COLUMN mode VARCHAR(20) NOT NULL DEFAULT 'agent'"
                    )
                )
        if "model_name" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE chat_sessions ADD COLUMN model_name VARCHAR(100)")
                )

    if "agent_usage" in table_names:
        columns = {column["name"] for column in inspector.get_columns("agent_usage")}
        if "session_id" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE agent_usage ADD COLUMN session_id INTEGER")
                )
        if "phase" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE agent_usage ADD COLUMN phase VARCHAR(24) NOT NULL DEFAULT 'thinking'"
                    )
                )
        if "domain" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE agent_usage ADD COLUMN domain VARCHAR(32)")
                )
