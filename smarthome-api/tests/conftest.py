import os
from pathlib import Path

import pytest

TEST_DB = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["UPLOAD_DIR"] = str(Path(__file__).parent / "uploads")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-sufficient-length")

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401, E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    yield
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)
