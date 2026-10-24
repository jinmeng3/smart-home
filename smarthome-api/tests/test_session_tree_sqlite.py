"""会话树 SQLite 存储测试。

覆盖 ``SqliteSessionRepo`` / ``SqliteSessionStorage`` 的持久化往返、``find_metadata``、
分叉、删除与 ``close()``，补回此前缺失的 SQLite 路径覆盖。
"""

from __future__ import annotations

import pytest
from app.db.base import Base
from app.session_tree import SqliteSessionRepo
from app.session_tree.errors import SessionError
from app.session_tree.session.types import CreateOptions, EntryQuery, ForkOptions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def repo(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'sessions.db'}")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return SqliteSessionRepo(factory)


def _user(text: str) -> dict:
    return {"role": "user", "content": [{"type": "text", "text": text}], "timestamp": 1}


def _assistant(text: str) -> dict:
    return {
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "timestamp": 1,
    }


def _path(session) -> list:
    return session.find_entries_on_branch(
        EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
    )


def test_create_and_find_metadata(repo):
    session = repo.create(CreateOptions(session_key="demo"))
    session.append_message(_user("hello"))
    session.close()

    metadata = repo.find_metadata("demo")
    assert metadata is not None
    assert metadata.session_key == "demo"
    assert repo.find_metadata("missing") is None


def test_persistence_roundtrip(repo):
    session = repo.create(CreateOptions(session_key="roundtrip"))
    session.append_message(_user("hello"))
    session.append_message(_assistant("world"))
    session.close()

    reopened = repo.open(repo.find_metadata("roundtrip"))
    try:
        entries = _path(reopened)
        assert len(entries) == 2
        assert entries[0].message["content"][0]["text"] == "hello"
        assert entries[1].message["content"][0]["text"] == "world"
    finally:
        reopened.close()


def test_fork_tree(repo):
    session = repo.create(CreateOptions(session_key="src"))
    session.append_message(_user("hello"))
    session.append_message(_assistant("world"))
    session.close()

    forked = repo.fork(
        repo.find_metadata("src"),
        ForkOptions(scope="tree"),
        CreateOptions(session_key="forked"),
    )
    try:
        assert len(_path(forked)) == 2
    finally:
        forked.close()


def test_delete(repo):
    session = repo.create(CreateOptions(session_key="del"))
    session.close()

    repo.delete(repo.find_metadata("del"))
    assert repo.find_metadata("del") is None


def test_create_duplicate_raises(repo):
    repo.create(CreateOptions(session_key="dup")).close()
    with pytest.raises(SessionError):
        repo.create(CreateOptions(session_key="dup"))
