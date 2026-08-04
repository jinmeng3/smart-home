import json
from typing import cast

import bcrypt
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.scene import SceneTemplate
from app.models.user import User
from app.models.room import Room


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_ai_model_settings()
    migrate_device_group_column()
    migrate_room_columns()


def migrate_room_columns() -> None:
    """为已有开发数据库补充房间弹窗所需列。"""
    columns = {column["name"] for column in inspect(engine).get_columns("rooms")}
    definitions = {
        "icon": "VARCHAR(40) NOT NULL DEFAULT 'room'",
        "theme_color": "VARCHAR(16) NOT NULL DEFAULT '#3478f6'",
        "version": "INTEGER NOT NULL DEFAULT 1",
    }
    with engine.begin() as connection:
        for name, definition in definitions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE rooms ADD COLUMN {name} {definition}"))


def migrate_ai_model_settings() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("ai_models")}

    with engine.begin() as connection:
        if "temperature" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE ai_models ADD COLUMN temperature "
                    "FLOAT NOT NULL DEFAULT 0.7"
                )
            )

        if "max_tokens" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE ai_models ADD COLUMN max_tokens "
                    "INTEGER NOT NULL DEFAULT 4096"
                )
            )


def migrate_device_group_column() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("devices")}

    if "group_id" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE devices ADD COLUMN group_id INTEGER NULL "
                    "REFERENCES device_group(id) ON DELETE SET NULL"
                )
            )


def seed_demo_data(db: Session) -> None:
    demo_password_hash = bcrypt.hashpw(b"123456", bcrypt.gensalt()).decode("utf-8")
    user = db.scalar(select(User).where(User.email == "zhang.xm@company.com"))

    if not user:
        user = User(
            name="张晓明",
            email="zhang.xm@company.com",
            password_hash=demo_password_hash,
        )
        db.add(user)
        db.flush()

    member = db.scalar(select(User).where(User.email == "member@example.com"))

    if not member:
        member = User(
            name="家庭成员",
            email="member@example.com",
            password_hash=demo_password_hash,
        )
        db.add(member)
        db.flush()

    outsider = db.scalar(select(User).where(User.email == "outsider@example.com"))

    if not outsider:
        db.add(
            User(
                name="访客用户",
                email="outsider@example.com",
                password_hash=demo_password_hash,
            )
        )

    household = db.scalar(
        select(Household).where(
            Household.name == "星河公寓", Household.created_by == user.id
        )
    )

    if not household:
        household = Household(
            name="星河公寓",
            address="上海市浦东新区",
            timezone="Asia/Shanghai",
            created_by=user.id,
        )
        db.add(household)
        db.flush()

    membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.household_id == household.id,
            HouseholdMembership.user_id == user.id,
        ),
    )

    if not membership:
        db.add(
            HouseholdMembership(
                household_id=household.id, user_id=user.id, role=HouseholdRole.ADMIN
            )
        )

    member_membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.household_id == household.id,
            HouseholdMembership.user_id == member.id,
        ),
    )

    if not member_membership:
        db.add(
            HouseholdMembership(
                household_id=household.id,
                user_id=member.id,
                role=HouseholdRole.MEMBER,
            )
        )

    seed_scene_templates(db)
    seed_rooms(db, household.id)

    db.commit()


def seed_rooms(db: Session, household_id: int) -> None:
    if db.scalar(select(Room).where(Room.household_id == household_id)):
        return
    rooms = [
        ("客厅", "living", 28.6, 8, 24.2, 55, 18, 82),
        ("主卧", "bedroom", 22.4, 6, 23, 52, 16, 86),
        ("次卧", "bedroom", 16.8, 5, 25, 60, 28, 78),
        ("厨房", "kitchen", 12.5, 7, 25, 58, 20, 84),
        ("书房", "study", 15.2, 5, 24, 50, 22, 80),
        ("阳台", "balcony", 9.8, 4, 28, 65, 30, 88),
    ]
    for index, (name, room_type, area, count, temp, humidity, pm25, comfort) in enumerate(rooms):
        db.add(Room(
            household_id=household_id, name=name, floor="1F", room_type=room_type,
            area=area, comfort=comfort, temperature=temp, humidity=humidity,
            pm25=pm25, illuminance=320 + index * 25, noise=42 - index,
            device_count=count, online_count=count,
            device_states=json.dumps({"light": index in (0, 2, 3), "airConditioner": index in (0, 1, 4), "curtain": index != 1, "socket": index < 4}, ensure_ascii=False),
        ))


def seed_scene_templates(db: Session) -> None:
    """写入场景页可直接使用的推荐模板，已存在的数据保持不变。"""
    templates = [
        {
            "id": "romantic-dinner",
            "name": "浪漫晚餐模式",
            "description": "营造温馨浪漫的晚餐氛围",
            "icon": "light",
            "color": "var(--color-warning)",
            "trigger_type": "manual",
            "trigger_label": "手动执行",
            "category": "娱乐",
            "room_labels": ["餐厅", "客厅"],
            "recommended": True,
            "steps": [
                {
                    "name": "调暗餐厅灯光 40%",
                    "description": "餐厅灯 · 亮度 40%",
                    "deviceId": "dining-light",
                    "order": 1,
                },
                {
                    "name": "播放晚餐歌单",
                    "description": "客厅音箱 · 晚餐歌单",
                    "deviceId": "living-speaker",
                    "order": 2,
                },
            ],
        },
        {
            "id": "sleep-security",
            "name": "安心睡眠模式",
            "description": "关闭公共区域设备并启用夜间安防",
            "icon": "eye",
            "color": "var(--color-scene-sleep)",
            "trigger_type": "schedule",
            "trigger_label": "每日 23:00",
            "category": "睡眠",
            "room_labels": ["客厅", "卧室"],
            "recommended": True,
            "steps": [
                {
                    "name": "关闭客厅灯",
                    "description": "客厅灯 · 关",
                    "deviceId": "living-light",
                    "order": 1,
                },
                {
                    "name": "启用夜间摄像头",
                    "description": "摄像头 · 夜间安防",
                    "deviceId": "security-camera",
                    "order": 2,
                },
            ],
        },
    ]
    for sort_order, data in enumerate(templates, 10):
        if db.get(SceneTemplate, data["id"]):
            continue
        steps = cast("list[dict[str, str | int]]", data.pop("steps"))
        rooms = cast("list[str]", data.pop("room_labels"))
        db.add(
            SceneTemplate(
                **data,
                room_labels=json.dumps(rooms, ensure_ascii=False),
                device_count=len({step["deviceId"] for step in steps}),
                steps_json=json.dumps(steps, ensure_ascii=False),
                sort_order=sort_order,
            )
        )
