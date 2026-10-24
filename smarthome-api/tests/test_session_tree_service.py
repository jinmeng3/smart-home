"""``app.services.session_tree`` 接入层测试。

覆盖：会话树消息镜像、压缩上下文读取、以及超限触发压缩。
"""

from __future__ import annotations

from app.services import session_tree as svc
from app.session_tree import InMemorySessionRepo
from app.session_tree.session.types import CompactionSettings, EntryQuery


def _patch_repo(monkeypatch):
    """用内存仓库替换服务默认的 SQLite 仓库，避免依赖真实数据库。"""
    repo = InMemorySessionRepo()
    monkeypatch.setattr(svc, "get_tree_repo", lambda: repo)
    return repo


def _fake_summarizer(text: str = "SUMMARY"):
    def summarizer(system, user, *, max_tokens=None, isolation_id=None):
        return text, {"input": 10, "output": 5, "totalTokens": 15}

    return summarizer


def test_session_key_for():
    assert svc.session_key_for(42) == "chat:42"


def test_mirror_messages_builds_context(monkeypatch):
    _patch_repo(monkeypatch)

    svc.mirror_user_message(1, "开灯")
    svc.mirror_assistant_message(1, "好的，已为你打开灯")

    messages = svc.build_context_messages(1)
    assert len(messages) == 2
    assert messages[0].content == "开灯"
    assert messages[1].content == "好的，已为你打开灯"


def test_mirror_subagent_writes_custom_entry(monkeypatch):
    _patch_repo(monkeypatch)

    svc.mirror_user_message(1, "查一下设备状态")
    svc.mirror_subagent(
        1, "device", "查一下设备状态", "设备状态正常", data={"devices": 3}
    )

    session = svc.get_or_create_tree_session(1)
    try:
        entries = session.find_entries_on_branch(
            EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
        )
        custom = [e for e in entries if e.type == "custom"]
        assert len(custom) == 1
        assert custom[0].custom_type == "subagent"
        assert custom[0].data["domain"] == "device"
    finally:
        session.close()

    # custom 节点不进对话历史，仅保留 user 消息
    messages = svc.build_context_messages(1)
    assert len(messages) == 1
    assert messages[0].content == "查一下设备状态"


def test_compact_if_needed_triggers(monkeypatch):
    _patch_repo(monkeypatch)

    for _ in range(6):
        svc.mirror_user_message(1, "a" * 40)
        svc.mirror_assistant_message(1, "b" * 40)

    compacted = svc.compact_if_needed(
        1,
        summarizer=_fake_summarizer(),
        context_window=150,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=50, keep_recent_tokens=20
        ),
    )
    assert compacted is True

    session = svc.get_or_create_tree_session(1)
    try:
        entries = session.find_entries_on_branch(
            EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
        )
        assert entries[-1].type == "compaction"
    finally:
        session.close()


def test_compact_if_needed_skips_when_small(monkeypatch):
    _patch_repo(monkeypatch)

    svc.mirror_user_message(1, "hello")
    svc.mirror_assistant_message(1, "hi")

    compacted = svc.compact_if_needed(
        1,
        summarizer=_fake_summarizer(),
        context_window=100000,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert compacted is False


def test_load_tree_history_success_clears_checkpointer(monkeypatch):
    import asyncio

    from app.agents.agent_service import runner as runner_mod
    from langchain_core.messages import HumanMessage

    deleted = {}

    class FakeSaver:
        async def adelete_thread(self, thread_id):
            deleted["thread_id"] = thread_id

    async def fake_get_checkpointer():
        return FakeSaver()

    monkeypatch.setattr(
        runner_mod, "build_context_messages", lambda sid: [HumanMessage(content="hi")]
    )
    monkeypatch.setattr(runner_mod, "get_checkpointer", fake_get_checkpointer)

    history = asyncio.run(runner_mod._load_tree_history(1, "thread-1"))
    assert history is not None
    assert len(history) == 1
    assert history[0].content == "hi"
    assert deleted["thread_id"] == "thread-1"


def test_load_tree_history_falls_back_on_error(monkeypatch):
    import asyncio

    from app.agents.agent_service import runner as runner_mod

    def boom(sid):
        raise RuntimeError("tree read failed")

    monkeypatch.setattr(runner_mod, "build_context_messages", boom)

    history = asyncio.run(runner_mod._load_tree_history(1, "thread-1"))
    assert history is None
