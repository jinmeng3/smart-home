"""``app.compaction`` 编排层测试。

覆盖：序列化 / 截断、usage 合并、触发判定、压缩（非 split / split / 迭代更新）、
分支摘要、扩展钩子、摘要请求的重试与取消。
"""

from __future__ import annotations

import pytest
from app.compaction import (
    CompactionEngine,
    combine_usage,
    serialize_conversation,
    truncate_tool_result,
    usage_from_metadata,
)
from app.compaction.events import (
    BeforeBranchSummaryResult,
    BeforeCompactResult,
    CompactionHooks,
)
from app.compaction.prompts import UPDATE_SUMMARIZATION_PROMPT
from app.compaction.summarize import SummarizationAborted, complete_summarization
from app.session_tree import InMemorySessionRepo, build_session_context
from app.session_tree.session.types import CompactionSettings, EntryQuery

# === 消息 / 会话构造 ===


def _user(text: str) -> dict:
    return {"role": "user", "content": [{"type": "text", "text": text}], "timestamp": 1}


def _assistant(
    text: str, *, usage: dict | None = None, tools: list | None = None
) -> dict:
    content = [{"type": "text", "text": text}]
    if tools:
        content.extend(tools)
    message = {"role": "assistant", "content": content, "timestamp": 1}
    if usage is not None:
        message["usage"] = usage
    return message


def _tool_result(text: str) -> dict:
    return {"role": "toolResult", "content": text, "timestamp": 1}


def _tool_call(name: str, args: dict) -> dict:
    return {"type": "toolCall", "name": name, "arguments": args}


def _session(*messages: dict):
    repo = InMemorySessionRepo()
    session = repo.create()
    for message in messages:
        session.append_message(message)
    return session


class FakeSummarizer:
    """记录每次调用的假摘要器，返回固定文本。"""

    def __init__(self, text: str = "SUMMARY", *, usage: dict | None = None) -> None:
        self.text = text
        self.usage = usage or {"input": 10, "output": 5, "totalTokens": 15}
        self.calls: list[dict] = []

    def __call__(self, system, user, *, max_tokens=None, isolation_id=None):
        self.calls.append(
            {
                "system": system,
                "user": user,
                "max_tokens": max_tokens,
                "isolation_id": isolation_id,
            }
        )
        return self.text, self.usage


# === 序列化 / usage ===


def test_serialize_conversation_covers_roles():
    messages = [
        _user("turn on the light"),
        _assistant("ok", tools=[_tool_call("read", {"path": "a.txt"})]),
        _tool_result("file content"),
    ]
    text = serialize_conversation(messages)
    assert "[User]: turn on the light" in text
    assert "[Assistant]: ok" in text
    assert 'read(path="a.txt")' in text
    assert "[Tool result]: file content" in text


def test_truncate_tool_result_keeps_prefix():
    long_text = "x" * 2500
    truncated = truncate_tool_result(long_text)
    assert truncated.endswith("[500 more characters truncated]")
    assert truncated.startswith("x" * 2000)
    assert truncate_tool_result("short") == "short"


def test_combine_usage_sums_fields():
    combined = combine_usage(
        {"input": 1, "output": 2, "totalTokens": 3},
        {"input": 4, "output": 5, "totalTokens": 9},
    )
    assert combined == {"input": 5, "output": 7, "totalTokens": 12}


def test_combine_usage_all_none_is_none():
    assert combine_usage(None, None) is None


def test_usage_from_metadata_normalizes_langchain():
    usage = usage_from_metadata(
        {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    )
    assert usage == {
        "input": 10,
        "output": 5,
        "cacheRead": 0,
        "cacheWrite": 0,
        "totalTokens": 15,
    }
    assert usage_from_metadata(None) is None


# === 触发判定 ===


def test_evaluate_triggers_at_threshold():
    session = _session(
        _user("hello"),
        _assistant("hi", usage={"totalTokens": 100}),
    )
    engine = CompactionEngine(FakeSummarizer())
    decision = engine.evaluate(
        session,
        context_window=120,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=50, keep_recent_tokens=20
        ),
    )
    assert decision.should_compact is True
    assert decision.reason == "threshold"


def test_evaluate_disabled():
    session = _session(_user("hello"))
    engine = CompactionEngine(FakeSummarizer())
    decision = engine.evaluate(
        session,
        context_window=120,
        settings=CompactionSettings(enabled=False),
    )
    assert decision.reason == "disabled"
    assert decision.should_compact is False


def test_evaluate_nothing_to_compact_when_empty():
    session = _session()
    engine = CompactionEngine(FakeSummarizer())
    decision = engine.evaluate(session, context_window=120)
    assert decision.reason == "nothing_to_compact"


def test_evaluate_aborted_skips():
    session = _session(_user("hello"), _assistant("hi"))
    engine = CompactionEngine(FakeSummarizer())
    decision = engine.evaluate(
        session,
        context_window=120,
        last_assistant_message={"role": "assistant", "stopReason": "aborted"},
    )
    assert decision.reason == "aborted"


# === 压缩 ===


def test_compact_appends_entry_and_rebuilds():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
    )
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )

    assert result.entry_id is not None
    assert result.summary.startswith("SUMMARY")
    assert result.is_split_turn is False

    entries = session.find_entries_on_branch(
        EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
    )
    assert entries[-1].type == "compaction"
    assert entries[-1].summary == result.summary

    # 上下文重建后只保留最后一个 compaction 条目 + retained_tail
    context = build_session_context(entries)
    assert context["messages"][0]["role"] == "compactionSummary"
    assert len(context["messages"]) == 3  # summary + 2 retained messages


def test_compact_iterative_uses_update_prompt():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
    )
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    settings = CompactionSettings(
        enabled=True, reserve_tokens=100, keep_recent_tokens=20
    )

    first = engine.compact(session, settings=settings)
    assert first.entry_id is not None

    # 追加新消息后再压缩，应使用更新式提示词
    session.append_message(_user("e" * 40))
    session.append_message(_assistant("f" * 40))
    second = engine.compact(session, settings=settings)
    assert second.entry_id is not None

    user_prompt = summarizer.calls[-1]["user"]
    assert "<previous-summary>" in user_prompt
    assert UPDATE_SUMMARIZATION_PROMPT.splitlines()[0] in user_prompt


def test_compact_split_turn_merges_two_summaries():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
        _user("e" * 40),
        _assistant("f" * 40),
    )
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=30
        ),
    )

    assert result.is_split_turn is True
    assert len(summarizer.calls) == 2
    assert "Turn Context (split turn):" in result.summary


def test_compact_nothing_to_summarize_does_not_call_llm():
    session = _session(_user("hello"), _assistant("hi"))
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=10000
        ),
    )
    assert result.reason == "nothing_to_compact"
    assert result.entry_id is None
    assert summarizer.calls == []


def test_compact_records_file_operations():
    session = _session(
        _user("read the file please"),
        _assistant(
            "let me check",
            tools=[
                _tool_call("read", {"path": "a.txt"}),
                _tool_call("edit", {"path": "b.py"}),
            ],
        ),
        _tool_result("file contents here"),
        _user("thanks"),
        _assistant("you're welcome"),
    )
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=10
        ),
    )

    assert "<read-files>\na.txt\n</read-files>" in result.summary
    assert "<modified-files>\nb.py\n</modified-files>" in result.summary

    entries = session.find_entries_on_branch(
        EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
    )
    details = entries[-1].details
    assert details["readFiles"] == ["a.txt"]
    assert details["modifiedFiles"] == ["b.py"]


def test_compact_before_hook_cancels():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
    )
    summarizer = FakeSummarizer()

    def cancel(event):
        return BeforeCompactResult(cancel=True)

    engine = CompactionEngine(
        summarizer,
        hooks=CompactionHooks(before_compact=[cancel]),
    )
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert result.aborted is True
    assert result.entry_id is None
    assert summarizer.calls == []


def test_compact_after_hook_receives_event():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
    )
    events = []

    def after(event):
        events.append(event)

    engine = CompactionEngine(
        FakeSummarizer(),
        hooks=CompactionHooks(after_compact=[after]),
    )
    engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert len(events) == 1
    assert events[0].entry_id is not None


# === 分支摘要 ===


def _branched_session():
    repo = InMemorySessionRepo()
    session = repo.create()
    root = session.append_message(_user("root"))
    main_leaf = session.append_message(_assistant("on main"))
    session.create_lane("alt", at=root)
    alt_leaf = session.view("alt").append_message(_user("another path"))
    return session, root, main_leaf, alt_leaf


def test_generate_branch_summary_produces_preamble():
    session, _root, main_leaf, alt_leaf = _branched_session()
    summarizer = FakeSummarizer()
    engine = CompactionEngine(summarizer)
    result = engine.generate_branch_summary(
        session,
        old_leaf_id=main_leaf,
        target_id=alt_leaf,
        context_window=1000,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert result.summary.startswith(
        "The user explored a different conversation branch"
    )
    assert "SUMMARY" in result.summary


def test_summarize_branch_appends_entry_at_target():
    session, _root, main_leaf, alt_leaf = _branched_session()
    engine = CompactionEngine(FakeSummarizer())
    result = engine.summarize_branch(
        session,
        old_leaf_id=main_leaf,
        target_id=alt_leaf,
        context_window=1000,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )

    assert result.entry_id is not None
    entries = session.find_entries_on_branch(
        EntryQuery(start=result.entry_id, order="oldestFirst")
    )
    last = entries[-1]
    assert last.type == "branch_summary"
    assert last.from_id == main_leaf


def test_summarize_branch_before_hook_cancels():
    session, _root, main_leaf, alt_leaf = _branched_session()

    def cancel(event):
        return BeforeBranchSummaryResult(cancel=True)

    engine = CompactionEngine(
        FakeSummarizer(),
        hooks=CompactionHooks(before_branch_summary=[cancel]),
    )
    result = engine.summarize_branch(
        session,
        old_leaf_id=main_leaf,
        target_id=alt_leaf,
        context_window=1000,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert result.aborted is True
    assert result.entry_id is None


# === 摘要请求：重试 / 取消 ===


def test_complete_summarization_retries_transient_errors():
    state = {"attempts": 0}

    def flaky(system, user, *, max_tokens=None, isolation_id=None):
        state["attempts"] += 1
        if state["attempts"] <= 2:
            raise RuntimeError("transient")
        return "ok", None

    text, _usage = complete_summarization(flaky, "sys", "usr", retry_attempts=2)
    assert text == "ok"
    assert state["attempts"] == 3


def test_complete_summarization_abort_not_retried():
    def boom(system, user, *, max_tokens=None, isolation_id=None):
        raise SummarizationAborted("aborted")

    with pytest.raises(SummarizationAborted):
        complete_summarization(boom, "sys", "usr", retry_attempts=5)


def test_complete_summarization_honors_is_aborted():
    def noop(system, user, *, max_tokens=None, isolation_id=None):
        return "ok", None

    with pytest.raises(SummarizationAborted):
        complete_summarization(noop, "sys", "usr", is_aborted=lambda: True)


def test_engine_compact_aborts_on_aborted_summarizer():
    session = _session(
        _user("a" * 40),
        _assistant("b" * 40),
        _user("c" * 40),
        _assistant("d" * 40),
    )

    def boom(system, user, *, max_tokens=None, isolation_id=None):
        raise SummarizationAborted("aborted")

    engine = CompactionEngine(boom)
    result = engine.compact(
        session,
        settings=CompactionSettings(
            enabled=True, reserve_tokens=100, keep_recent_tokens=20
        ),
    )
    assert result.aborted is True
    assert result.entry_id is None
