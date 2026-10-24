"""测试全局夹具。

策略：
- 使用内存 SQLite，每个测试用例开始前重建表。
- 重写 ``app.db.session.engine`` 与 ``SessionLocal`` 指向测试库。
- 重写 ``app.agents.audit.recorder._AuditRecorder._ensure_writer`` 的副作用：
  让审计文件落到临时目录，测试结束后清理。
- 通过 ``fastapi.testclient.TestClient`` 调用接口，避开 ``services`` 模块的循环导入。
"""
from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Generator
from contextlib import suppress
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 测试需要的开关：禁用 funnel 语义向量层、关闭生产模式、避免审计目录污染项目根。
os.environ.setdefault("PRODUCTION_MODE", "false")
os.environ.setdefault("FUNNEL_SEMANTIC_ENABLED", "false")
os.environ.setdefault("UPLOAD_DIR", "app/uploads-test")
os.environ.setdefault("AUDIT_DIR", "agent_audit-test")

from app.db import session as db_session
from app.db.base import Base
from app.main import app


@pytest.fixture(scope="session")
def _test_engine():
    """会话级内存 SQLite 引擎（多连接共享同一内存库）。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def _override_db(_test_engine):
    """把全局 engine / SessionLocal 替换为内存 SQLite。"""
    test_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=_test_engine
    )
    original_engine = db_session.engine
    original_factory = db_session.SessionLocal
    db_session.engine = _test_engine
    db_session.SessionLocal = test_session_factory

    # FastAPI 路由通过 ``DB_DEPENDENCY = Depends(get_db)`` 在 import 时就捕获了原始函数，
    # 直接改写模块属性不会生效；这里按原始函数对象注册依赖覆盖，效果等价且不影响全局。
    from app.api import deps

    original_get_db = deps.get_db

    def _get_db_override() -> Generator[Session, None, None]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[original_get_db] = _get_db_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(original_get_db, None)
        db_session.engine = original_engine
        db_session.SessionLocal = original_factory


@pytest.fixture(autouse=True)
def _isolated_dirs(monkeypatch):
    """把上传 / 审计目录临时化，测试后清理。"""
    tmp = tempfile.mkdtemp(prefix="smarthome-test-")
    uploads = Path(tmp) / "uploads"
    uploads.mkdir()
    audit = Path(tmp) / "audit"
    audit.mkdir()

    from app.core import config as config_mod

    real_settings_cls = config_mod.Settings
    settings_instance = real_settings_cls()
    settings_instance.upload_dir = str(uploads)
    settings_instance.audit_dir = str(audit)

    # FastAPI Depends 在 import 时捕获了 get_settings，这里用 app.dependency_overrides
    # 重定向依赖入口，确保请求处理时拿到隔离的 settings。
    app.dependency_overrides[config_mod.get_settings] = lambda: settings_instance
    # 清掉 lru_cache，避免上次调用的 settings 被复用
    try:
        config_mod.get_settings.cache_clear()
    except AttributeError:
        pass

    yield {"uploads": uploads, "audit": audit}
    app.dependency_overrides.pop(config_mod.get_settings, None)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session_obj(_test_engine):
    """直接拿到测试 Session，便于插入/查询。"""
    SessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 子代理 / 规则层测试需要的轻量 fixture
# 补充：test_rule_layer.py / test_funnel_router.py / test_alias_hot_reload.py
#       依赖的 db / context / device_factory / settings 在 _override_db / make_user
#       之上加封装，不干扰原有 API 测试。
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(monkeypatch):
    """独立的 Settings 实例。

    FunnelRouter / AliasIndex 等模块会 ``from app.core.config import
    get_settings`` 拿到本地引用，所以只 patch ``app.core.config.get_settings``
    不够。要同时 patch 所有使用方模块的本地引用。

    注意：必须先拿到权威模块上 ``get_settings`` 的原函数引用（lru_cache
    包装对象），再用这个原引用去与各模块属性 ``is`` 比较。**如果先 setattr
    了权威模块再比较，会出现「自己跟自己不等」的判断失败，导致没有任何
    使用方模块被 patch。**
    """
    from app.core import config as config_mod

    # 1. 记录原 get_settings 引用（lru_cache 包装对象）
    original_get_settings = config_mod.get_settings
    # 2. 清理原 cache，保证下面用同一个 fresh instance
    try:
        original_get_settings.cache_clear()
    except AttributeError:
        pass

    instance = config_mod.Settings()
    replacement = lambda: instance

    # 3. patch 权威模块
    monkeypatch.setattr(config_mod, "get_settings", replacement)

    # 4. patch 所有使用方模块：与**原引用** is 比较
    import sys
    patched: set[str] = set()
    for mod_name, mod in list(sys.modules.items()):
        if mod is None or not mod_name.startswith("app."):
            continue
        with suppress(Exception):
            if getattr(mod, "get_settings", None) is original_get_settings:
                monkeypatch.setattr(mod, "get_settings", replacement, raising=False)
                patched.add(mod_name)
    yield instance


@pytest.fixture()
def db(db_session_obj):
    """别名 fixture：让 test_rule_layer 写 `db` 跟 `db_session_obj` 拿到同一份 Session。"""
    return db_session_obj


@pytest.fixture()
def context(db):
    """构造一个 AgentContext，使用固定的 household_id=1 / user_id=1。"""
    from app.agents.context import AgentContext

    return AgentContext(
        user_id=1,
        household_id=1,
        session_id=1,
        auto_execute_low_risk=False,
        confirm_high_risk=True,
        language="zh-CN",
        detail_level=70,
        tools_enabled=True,
    )


@pytest.fixture()
def device_factory(db):
    """在测试 Session 里插入 Device，返回创建的 ORM 对象。

    为避免外键约束失败，首次调用时自动建一个默认 household。
    """
    from app.models.device import Device, DeviceStatus
    from app.models.household import Household
    from app.models.user import User

    counter = {"i": 0}
    ensured = {"household_id": None, "user_id": None}

    def _ensure_household(household_id: int) -> int:
        if ensured["household_id"] == household_id and ensured["user_id"] is not None:
            return household_id
        # 创建一个最小用户 + 家庭以满足外键
        user = User(
            email="household-fixture@example.com",
            name="household-fixture",
            password_hash="x",
            status="active",
        )
        db.add(user)
        db.flush()
        existing = db.get(Household, household_id)
        if existing is None:
            hh = Household(
                id=household_id,
                name="Fixture Home",
                address="",
                timezone="Asia/Shanghai",
                created_by=user.id,
            )
            db.add(hh)
            db.flush()
        ensured["user_id"] = user.id
        ensured["household_id"] = household_id
        return household_id

    def _factory(
        name: str,
        room: str,
        type: str = "light",
        device_id: str | None = None,
        household_id: int = 1,
        **kwargs,
    ):
        counter["i"] += 1
        _ensure_household(household_id)
        dev = Device(
            household_id=household_id,
            device_id=device_id or f"test-dev-{counter['i']}",
            name=name,
            room=room,
            type=type,
            brand=kwargs.get("brand", "test"),
            status=DeviceStatus.ONLINE,
            connection=kwargs.get("connection", "MQTT"),
            firmware=kwargs.get("firmware", "1.0.0"),
            icon=kwargs.get("icon"),
            color=kwargs.get("color"),
            image_url=kwargs.get("image_url"),
            group_id=kwargs.get("group_id"),
        )
        db.add(dev)
        db.flush()
        db.refresh(dev)
        return dev

    return _factory


@pytest.fixture()
def auth_headers():
    """返回 ``register_and_login(client, ...)`` 调用时使用的工具函数。"""
    return _bearer


@pytest.fixture()
def make_user(client: TestClient):
    """注册并登录一个用户，返回 (data, headers)。"""

    counter = {"i": 0}

    def _factory(email: str | None = None, name: str | None = None, password: str = "StrongP@ss1"):
        counter["i"] += 1
        i = counter["i"]
        email = email or f"user{i}@example.com"
        name = name or f"user{i}"
        reg = client.post(
            "/api/auth/register",
            json={"username": name, "email": email, "password": password},
        )
        assert reg.status_code == 200, reg.text
        # 重新走 login，使 SecurityDevice 被写入（只有 login 会注册当前设备）
        login = client.post(
            "/api/auth/login",
            json={"account": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = login.json()["data"]["accessToken"]
        return login.json()["data"], _bearer(token)

    return _factory


@pytest.fixture()
def make_household(client: TestClient, make_user):
    """创建用户并返回用户的家庭 ID 与默认头。"""

    counter = {"i": 0}

    def _factory(name: str = "My Home", timezone: str = "Asia/Shanghai"):
        counter["i"] += 1
        user_data, headers = make_user(
            email=f"house{counter['i']}@example.com",
            name=f"house{counter['i']}",
        )
        resp = client.post(
            "/api/households",
            headers=headers,
            json={"name": name, "timezone": timezone},
        )
        assert resp.status_code == 201, resp.text
        household_id = resp.json()["data"]["id"]
        return {
            "user": user_data,
            "headers": headers,
            "household_id": household_id,
        }

    return _factory


@pytest.fixture(autouse=True)
def _truncate_tables(_test_engine):
    """在每个测试开始前清空所有业务表（保留结构）。"""
    # 让 import 副作用完整就绪：路由解析时已经访问过这些模型。
    from app.models import (  # noqa: F401
        agent_lease,
        agent_usage,
        ai,
        automation,
        chat,
        device,
        household,
        membership,
        overview,
        room,
        scene,
        security,
        session_tree,
        user,
        user_preferences,
    )

    yield  # 测试结束后再清
    with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())