"""add household ownership and performance indexes

Revision ID: 20260807_01
Revises:
Create Date: 2026-08-07
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260807_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _first_household(connection) -> tuple[int, int]:
    row = connection.execute(
        sa.text("SELECT id, created_by FROM households ORDER BY id LIMIT 1")
    ).first()
    if row is None:
        raise RuntimeError("无法迁移历史数据：数据库中没有家庭")
    return int(row.id), int(row.created_by)


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "users" not in inspector.get_table_names():
        from app.db.base import Base
        import app.models  # noqa: F401

        Base.metadata.create_all(connection)
        return

    default_household_id, default_user_id = _first_household(connection)

    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("household_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_devices_household_id",
            "households",
            ["household_id"],
            ["id"],
            ondelete="CASCADE",
        )
    conflicts = connection.execute(
        sa.text(
            """
            SELECT rd.device_id
            FROM room_devices rd
            JOIN rooms r ON r.id = rd.room_id
            GROUP BY rd.device_id
            HAVING COUNT(DISTINCT r.household_id) > 1
            """
        )
    ).fetchall()
    if conflicts:
        raise RuntimeError(
            "设备被绑定到多个家庭，迁移已中止: "
            + ",".join(str(row.device_id) for row in conflicts)
        )
    connection.execute(
        sa.text(
            """
            UPDATE devices
            SET household_id = COALESCE(
                (SELECT MIN(r.household_id)
                 FROM room_devices rd JOIN rooms r ON r.id = rd.room_id
                 WHERE rd.device_id = devices.id),
                :default_household_id
            )
            """
        ),
        {"default_household_id": default_household_id},
    )
    with op.batch_alter_table("devices") as batch:
        batch.alter_column("household_id", existing_type=sa.Integer(), nullable=False)
        batch.create_index("ix_devices_household_id", ["household_id"])
        batch.create_index("ix_devices_household_status", ["household_id", "status"])
        batch.create_index("ix_devices_household_updated", ["household_id", "updated_at"])
        batch.create_index("ix_devices_group_id", ["group_id"])

    with op.batch_alter_table("device_group") as batch:
        batch.add_column(sa.Column("household_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_device_group_household_id",
            "households",
            ["household_id"],
            ["id"],
            ondelete="CASCADE",
        )
    connection.execute(
        sa.text(
            """
            UPDATE device_group
            SET household_id = COALESCE(
                (SELECT MIN(d.household_id) FROM devices d
                 WHERE d.group_id = device_group.id),
                :default_household_id
            )
            """
        ),
        {"default_household_id": default_household_id},
    )
    with op.batch_alter_table("device_group") as batch:
        batch.alter_column("household_id", existing_type=sa.Integer(), nullable=False)
        batch.create_index("ix_device_group_household_id", ["household_id"])
        batch.create_unique_constraint(
            "uq_device_group_household_name", ["household_id", "name"]
        )

    for table_name in ("scenes", "scene_drafts"):
        with op.batch_alter_table(table_name) as batch:
            batch.add_column(sa.Column("household_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                f"fk_{table_name}_household_id",
                "households",
                ["household_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch.create_foreign_key(
                f"fk_{table_name}_created_by",
                "users",
                ["created_by"],
                ["id"],
                ondelete="RESTRICT" if table_name == "scenes" else "CASCADE",
            )
        connection.execute(
            sa.text(
                f"UPDATE {table_name} SET household_id=:household_id, created_by=:user_id"
            ),
            {"household_id": default_household_id, "user_id": default_user_id},
        )
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column("household_id", existing_type=sa.Integer(), nullable=False)
            batch.alter_column("created_by", existing_type=sa.Integer(), nullable=False)
            batch.create_index(f"ix_{table_name}_household_id", ["household_id"])

    op.create_index("ix_scenes_household_sort", "scenes", ["household_id", "sort_order"])
    op.create_index("ix_scenes_household_updated", "scenes", ["household_id", "updated_at"])
    op.create_table(
        "scene_rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scene_id", sa.String(64), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("scene_id", "room_id", name="uq_scene_room"),
    )
    op.create_index("ix_scene_rooms_scene_id", "scene_rooms", ["scene_id"])
    op.create_index("ix_scene_rooms_room_id", "scene_rooms", ["room_id"])
    scene_rows = connection.execute(
        sa.text("SELECT id, household_id, room_names FROM scenes")
    ).fetchall()
    for scene_row in scene_rows:
        try:
            room_names = json.loads(scene_row.room_names or "[]")
        except json.JSONDecodeError:
            room_names = []
        if not isinstance(room_names, list) or not room_names:
            continue
        room_ids = connection.execute(
            sa.text(
                "SELECT id FROM rooms WHERE household_id=:household_id AND name IN :names"
            ).bindparams(sa.bindparam("names", expanding=True)),
            {"household_id": scene_row.household_id, "names": room_names},
        ).scalars()
        bindings = [
            {"scene_id": scene_row.id, "room_id": room_id}
            for room_id in room_ids
        ]
        if bindings:
            connection.execute(
                sa.text(
                    "INSERT INTO scene_rooms (scene_id, room_id) "
                    "VALUES (:scene_id, :room_id)"
                ),
                bindings,
            )
    op.create_index(
        "ix_automation_execution_status_time",
        "automation_executions",
        ["status", "started_at"],
    )
    if "auth_sessions" in inspector.get_table_names():
        op.drop_table("auth_sessions")
    for legacy_table in (
        "room_environment_reports",
        "device_data",
        "room_preferences",
    ):
        if legacy_table in inspector.get_table_names():
            op.drop_table(legacy_table)
    with op.batch_alter_table("ai_models") as batch:
        batch.alter_column("api_key", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("ai_models") as batch:
        batch.alter_column("api_key", existing_type=sa.Text(), nullable=False)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("device_name", sa.String(255)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.drop_index("ix_automation_execution_status_time", table_name="automation_executions")
    op.drop_index("ix_scenes_household_updated", table_name="scenes")
    op.drop_index("ix_scenes_household_sort", table_name="scenes")
    op.drop_index("ix_scene_rooms_room_id", table_name="scene_rooms")
    op.drop_index("ix_scene_rooms_scene_id", table_name="scene_rooms")
    op.drop_table("scene_rooms")
    for table_name in ("scene_drafts", "scenes"):
        with op.batch_alter_table(table_name) as batch:
            batch.drop_index(f"ix_{table_name}_household_id")
            batch.drop_constraint(f"fk_{table_name}_created_by", type_="foreignkey")
            batch.drop_constraint(f"fk_{table_name}_household_id", type_="foreignkey")
            batch.drop_column("created_by")
            batch.drop_column("household_id")
    with op.batch_alter_table("device_group") as batch:
        batch.drop_constraint("uq_device_group_household_name", type_="unique")
        batch.drop_index("ix_device_group_household_id")
        batch.drop_constraint("fk_device_group_household_id", type_="foreignkey")
        batch.drop_column("household_id")
    with op.batch_alter_table("devices") as batch:
        batch.drop_index("ix_devices_household_updated")
        batch.drop_index("ix_devices_household_status")
        batch.drop_index("ix_devices_household_id")
        batch.drop_index("ix_devices_group_id")
        batch.drop_constraint("fk_devices_household_id", type_="foreignkey")
        batch.drop_column("household_id")
