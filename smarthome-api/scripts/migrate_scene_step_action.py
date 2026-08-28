"""为 ``scene_steps`` 表添加 ``action`` 与 ``action_value`` 列。

用法：
    cd smarthome-api
    .venv/Scripts/python.exe scripts/migrate_scene_step_action.py

安全特性：
- 幂等：列已存在则跳过（基于 ``PRAGMA table_info``）。
- 仅对 ``scene_steps`` 表生效，不动其他表。
- 默认连 ``db/orion_home.db``（与 ``app.core.config.database_url`` 默认值一致）。

迁移完成后，``run_scene_service`` 会按 step.action 调对应 set_device_*，
NULL action 视为 ``"on"``（向后兼容历史数据）。
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "orion_home.db"


def has_column(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: 数据库文件不存在: {DB_PATH}")
        return 1
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        added = []
        if not has_column(cur, "scene_steps", "action"):
            cur.execute("ALTER TABLE scene_steps ADD COLUMN action VARCHAR(32)")
            added.append("action")
        else:
            print("[skip] scene_steps.action 已存在")
        if not has_column(cur, "scene_steps", "action_value"):
            cur.execute("ALTER TABLE scene_steps ADD COLUMN action_value REAL")
            added.append("action_value")
        else:
            print("[skip] scene_steps.action_value 已存在")
        conn.commit()
        if added:
            print(f"OK: 添加列 {added}")
        else:
            print("OK: 无需迁移")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
