"""会话树存储 + 上下文压缩的业务接入层。

把 ``app.session_tree``（树形会话存储）与 ``app.compaction``（压缩编排）接入到
聊天 / Agent 流程：用 ``ChatSession.id`` 作为会话树的 ``session_key``，把每轮对话
镜像为可分支、可压缩的树，并在上下文超限时触发压缩。

设计说明：
- 本层只做「镜像 + 压缩」，不改变 Agent 现有的 LangGraph checkpointer 历史机制；
  压缩后的精简上下文通过 ``build_context_messages`` 对外暴露，供后续接入。
- 每个操作独立打开 / 关闭树会话（释放 ORM 连接），调用方无需管理生命周期。
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.compaction import CompactionEngine
from app.compaction.summarize import Summarizer
from app.db.session import SessionLocal
from app.session_tree import SqliteSessionRepo
from app.session_tree.errors import SessionError
from app.session_tree.session.storage import Session, now_ms
from app.session_tree.session.types import CompactionSettings, CreateOptions

logger = logging.getLogger(__name__)


@lru_cache
def get_tree_repo() -> SqliteSessionRepo:
    """返回绑定到应用数据库的会话树仓库（进程内缓存）。"""
    return SqliteSessionRepo(SessionLocal)


def session_key_for(chat_session_id: int) -> str:
    """把 ``ChatSession.id`` 映射为会话树的 ``session_key``。"""
    return f"chat:{chat_session_id}"


def get_or_create_tree_session(chat_session_id: int) -> Session:
    """按 chat 会话 id 获取（不存在则创建）对应的会话树门面。"""
    repo = get_tree_repo()
    key = session_key_for(chat_session_id)

    metadata = repo.find_metadata(key)
    if metadata is not None:
        return repo.open(metadata)

    try:
        return repo.create(CreateOptions(session_key=key))
    except SessionError as exc:
        if exc.code != "already_exists":
            raise

    metadata = repo.find_metadata(key)
    if metadata is None:
        raise SessionError("not_found", f"Session tree not found: {key}")
    return repo.open(metadata)


# === 消息镜像 ===


def _user_message(text: str) -> dict:
    return {
        "role": "user",
        "content": [{"type": "text", "text": text}],
        "timestamp": now_ms(),
    }


def _assistant_message(text: str, usage: dict | None = None) -> dict:
    message = {
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "timestamp": now_ms(),
    }
    if usage:
        message["usage"] = usage
    return message


def _append_message(chat_session_id: int, message: dict) -> str:
    session = get_or_create_tree_session(chat_session_id)
    try:
        return session.append_message(message)
    finally:
        session.close()


def mirror_user_message(chat_session_id: int, text: str) -> str:
    """把用户消息镜像到会话树，返回树中的条目 id。"""
    return _append_message(chat_session_id, _user_message(text))


def mirror_assistant_message(
    chat_session_id: int, text: str, *, usage: dict | None = None
) -> str:
    """把助手回复镜像到会话树，返回树中的条目 id。"""
    return _append_message(chat_session_id, _assistant_message(text, usage))


def mirror_subagent(
    chat_session_id: int,
    domain: str,
    task: str,
    summary: str,
    *,
    data: dict | None = None,
    usage: dict | None = None,
) -> str:
    """把一次子 Agent 运行镜像为 custom 节点（供审计，不进对话历史）。

    ``build_context_messages`` 会跳过 custom 节点，因此不会污染 Agent 上下文；
    但该节点保留在树中，供审计与后续压缩钩子使用。
    """
    session = get_or_create_tree_session(chat_session_id)
    try:
        return session.append_custom_entry(
            "subagent",
            {
                "domain": domain,
                "task": task,
                "summary": summary,
                "data": data or {},
                "usage": usage or {},
            },
        )
    finally:
        session.close()


# === 上下文读取 ===


def build_context_messages(chat_session_id: int) -> list:
    """把会话树的（压缩后）上下文投影为 LangChain 消息列表。"""
    from langchain_core.messages import AIMessage, HumanMessage

    from app.session_tree import build_session_context
    from app.session_tree.messages import content_text
    from app.session_tree.session.types import EntryQuery

    session = get_or_create_tree_session(chat_session_id)
    try:
        path = session.find_entries_on_branch(
            EntryQuery(start=session.get_leaf_id(), order="oldestFirst")
        )
        context = build_session_context(path)
    finally:
        session.close()

    messages = []
    for message in context["messages"]:
        role = message.get("role")
        if role == "assistant":
            messages.append(AIMessage(content=content_text(message.get("content"))))
        elif role == "user":
            messages.append(HumanMessage(content=content_text(message.get("content"))))
        elif role == "compactionSummary":
            messages.append(
                HumanMessage(content=f"[Compaction summary]\n{message.get('summary', '')}")
            )
        elif role == "branchSummary":
            messages.append(
                HumanMessage(content=f"[Branch summary]\n{message.get('summary', '')}")
            )
        # toolResult / bashExecution / custom 等中间状态不进入对话历史
    return messages


# === 压缩 ===


def compact_if_needed(
    chat_session_id: int,
    *,
    summarizer: Summarizer,
    context_window: int,
    settings: CompactionSettings | None = None,
    max_tokens: int | None = None,
) -> bool:
    """上下文超限时压缩会话树，返回是否发生了压缩。"""
    session = get_or_create_tree_session(chat_session_id)
    try:
        engine = CompactionEngine(summarizer, max_tokens=max_tokens)
        decision = engine.evaluate(
            session, context_window=context_window, settings=settings
        )
        if not decision.should_compact:
            return False
        result = engine.compact(
            session,
            settings=settings,
            reason="threshold",
        )
        return result.entry_id is not None
    finally:
        session.close()
