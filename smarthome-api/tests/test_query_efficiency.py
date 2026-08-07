from sqlalchemy import event

from app.db.session import SessionLocal, engine
from app.models.automation import Automation
from app.models.device import Device, DeviceStatus
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.room import Room, RoomDevice
from app.models.user import User
from app.services.automation import list_automations_service
from app.services.room import list_rooms_service


def test_automation_list_uses_constant_query_count():
    with SessionLocal() as db:
        user = User(name="owner", email="owner@test.local", password_hash="unused")
        db.add(user)
        db.flush()
        household = Household(name="Home", created_by=user.id)
        db.add(household)
        db.flush()
        db.add(
            HouseholdMembership(
                household_id=household.id,
                user_id=user.id,
                role=HouseholdRole.ADMIN,
            )
        )
        db.add_all(
            Automation(
                household_id=household.id,
                name=f"automation-{index}",
                created_by=user.id,
            )
            for index in range(100)
        )
        household_id = household.id
        db.commit()

        statements = []

        def count_query(_conn, _cursor, statement, _params, _context, _many):
            if not statement.lstrip().upper().startswith("PRAGMA"):
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", count_query)
        try:
            result = list_automations_service(
                db, household_id, None, None, None, 1, 20
            )
        finally:
            event.remove(engine, "before_cursor_execute", count_query)

        assert result.total == 100
        assert len(result.items) == 20
        assert len(statements) <= 4, statements


def test_room_list_query_count_does_not_grow_with_rooms():
    with SessionLocal() as db:
        user = User(name="owner", email="rooms@test.local", password_hash="unused")
        db.add(user)
        db.flush()
        household = Household(name="Home", created_by=user.id)
        db.add(household)
        db.flush()
        db.add(
            HouseholdMembership(
                household_id=household.id,
                user_id=user.id,
                role=HouseholdRole.ADMIN,
            )
        )
        for index in range(100):
            room = Room(household_id=household.id, name=f"room-{index}")
            device = Device(
                household_id=household.id,
                device_id=f"device-{index}",
                name=f"device-{index}",
                room=room.name,
                type="light",
                brand="Demo",
                status=DeviceStatus.ONLINE,
                connection="Matter",
                firmware="1.0.0",
            )
            db.add_all([room, device])
            db.flush()
            db.add(RoomDevice(room_id=room.id, device_id=device.id))
        db.commit()
        user_id = user.id
        db.expire_all()
        user = db.get(User, user_id)

        statements = []

        def count_query(_conn, _cursor, statement, _params, _context, _many):
            if not statement.lstrip().upper().startswith("PRAGMA"):
                statements.append(statement)

        event.listen(engine, "before_cursor_execute", count_query)
        try:
            result = list_rooms_service(db, user)
        finally:
            event.remove(engine, "before_cursor_execute", count_query)

        assert result.total == 100
        assert len(statements) <= 2, statements
