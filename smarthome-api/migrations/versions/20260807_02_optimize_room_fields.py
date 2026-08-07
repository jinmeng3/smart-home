"""optimize room fields and constraints

Revision ID: 20260807_02
Revises: 20260807_01
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260807_02"
down_revision: Union[str, None] = "20260807_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    room_columns = {column["name"] for column in inspector.get_columns("rooms")}
    room_checks = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("rooms")
    }
    if (
        {"device_count", "online_count"} & room_columns
        or "created_at" not in room_columns
        or not {
            "ck_room_version_positive",
            "ck_room_area_non_negative",
            "ck_room_comfort_range",
        }.issubset(room_checks)
    ):
        with op.batch_alter_table("rooms") as batch_op:
            if "created_at" not in room_columns:
                batch_op.add_column(
                    sa.Column(
                        "created_at",
                        sa.DateTime(timezone=True),
                        server_default=sa.func.now(),
                        nullable=False,
                    )
                )
            if "online_count" in room_columns:
                batch_op.drop_column("online_count")
            if "device_count" in room_columns:
                batch_op.drop_column("device_count")
            if "ck_room_version_positive" not in room_checks:
                batch_op.create_check_constraint(
                    "ck_room_version_positive", "version >= 1"
                )
            if "ck_room_area_non_negative" not in room_checks:
                batch_op.create_check_constraint(
                    "ck_room_area_non_negative", "area >= 0"
                )
            if "ck_room_comfort_range" not in room_checks:
                batch_op.create_check_constraint(
                    "ck_room_comfort_range", "comfort BETWEEN 0 AND 100"
                )

    inspector = sa.inspect(connection)
    room_device_checks = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("room_devices")
    }
    if "ck_room_device_sort_order" not in room_device_checks:
        with op.batch_alter_table("room_devices") as batch_op:
            batch_op.create_check_constraint(
                "ck_room_device_sort_order", "sort_order >= 0"
            )


def downgrade() -> None:
    with op.batch_alter_table("room_devices") as batch_op:
        batch_op.drop_constraint("ck_room_device_sort_order", type_="check")

    with op.batch_alter_table("rooms") as batch_op:
        batch_op.drop_constraint("ck_room_comfort_range", type_="check")
        batch_op.drop_constraint("ck_room_area_non_negative", type_="check")
        batch_op.drop_constraint("ck_room_version_positive", type_="check")
        batch_op.add_column(
            sa.Column("device_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("online_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.drop_column("created_at")
