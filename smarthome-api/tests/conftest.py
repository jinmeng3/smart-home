from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.main import app
from app.models.household import Household
from app.models.membership import HouseholdMembership, HouseholdRole
from app.models.user import User


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_dir=str(tmp_path / "uploads"),
        development_mode=False,
    )


@pytest.fixture
def db(test_settings: Settings) -> Generator[Session, None, None]:
    engine = create_engine(test_settings.database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        admin = User(id=1, name="张晓明", email="zhang.xm@company.com")
        member = User(id=2, name="李雷", email="member@example.com")
        outsider = User(id=3, name="王芳", email="outsider@example.com")
        household = Household(id=1, name="星河公寓", address="上海市浦东新区", timezone="Asia/Shanghai", created_by=1)
        session.add_all([admin, member, outsider, household])
        session.flush()
        session.add(HouseholdMembership(id=1, household_id=1, user_id=1, role=HouseholdRole.ADMIN))
        session.commit()
        yield session

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session, test_settings: Settings) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
