from app.db.base import Base
from app.db.session import engine


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_devices_color()


def _migrate_devices_color() -> None:
    """为已存在的 devices 表添加 color 列（迁移）。"""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("devices")]
    if "color" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE devices ADD COLUMN color VARCHAR(16) NOT NULL DEFAULT '#6b7280'"))
            conn.commit()
