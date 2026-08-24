"""会话树存储的数据模型。

三类数据（与文档一致）：

- ``Entry``：会话内容树节点（7 种类型），带 ``parent_id`` 形成有向树。
- ``Record``：车道操作日志（9 种类型），挂在 lane 上，用于崩溃恢复与审计。
- Fact：全局事实（会话名、条目标签），以 ``Mutation(kind="fact")`` 表达。

三者共享同一个全局单调递增的 ``seq`` 序列号。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# 消息在存储层中作为不透明的 JSON 兼容字典保存；context / compaction 模块
# 按需读取其中的已知字段。
Message = dict[str, Any]
JsonValue = Any

EntryType = Literal[
    "message",
    "model_change",
    "thinking_level_change",
    "active_tools_change",
    "compaction",
    "branch_summary",
    "custom",
]

RecordType = Literal[
    "operation_started",
    "abort_requested",
    "operation_finished",
    "step_attempt",
    "tool_started",
    "queue_enqueued",
    "queue_cancelled",
    "write_deferred",
    "usage",
]

EntryOrder = Literal["newestFirst", "oldestFirst"]


@dataclass
class Entry:
    """树节点。``type`` 为判别字段，其余字段按类型可选。

    各类型对应的专属字段：

    - ``message``: message, terminate
    - ``model_change``: provider, model_id
    - ``thinking_level_change``: thinking_level
    - ``active_tools_change``: active_tool_names
    - ``compaction``: summary, retained_tail, tokens_before, details, usage
    - ``branch_summary``: from_id, summary, details, usage
    - ``custom``: custom_type, data
    """

    type: str
    id: str
    # 存储层分配（追加时覆盖）：parent_id / seq / timestamp
    seq: int = 0
    parent_id: str | None = None
    timestamp: int = 0

    # message
    message: Message | None = None
    terminate: bool | None = None

    # model_change
    provider: str | None = None
    model_id: str | None = None

    # thinking_level_change
    thinking_level: str | None = None

    # active_tools_change
    active_tool_names: list[str] | None = None

    # compaction
    summary: str | None = None
    retained_tail: list[Message] | None = None
    tokens_before: int | None = None
    details: JsonValue = None
    usage: JsonValue = None

    # branch_summary
    from_id: str | None = None

    # custom
    custom_type: str | None = None
    data: JsonValue = None


@dataclass
class Record:
    """车道操作日志。``type`` 为判别字段，``lane`` 必填。

    各类型对应的专属字段：

    - ``operation_started``: source_leaf_id, intent
    - ``abort_requested``: run_id
    - ``operation_finished``: run_id, outcome, error
    - ``step_attempt``: run_id, step, attempt, result_entry_id, compaction_reason
    - ``tool_started``: run_id, assistant_entry_id, tool_index, tool_call_id,
      tool_name, effective_args, result_entry_id, replay
    - ``queue_enqueued``: queue, run_id, target
    - ``queue_cancelled``: run_id, entry_id
    - ``write_deferred``: run_id, target
    - ``usage``: usage, cause, run_id, entry_id, attempt, stop_reason, tool_call_id, details
    """

    type: str
    id: str
    lane: str
    # 存储层分配（追加时覆盖）：seq / timestamp
    seq: int = 0
    timestamp: int = 0

    # operation_started
    source_leaf_id: str | None = None
    intent: JsonValue = None

    # abort_requested / operation_finished / step_attempt / tool_started /
    # queue_enqueued / queue_cancelled / write_deferred / usage
    run_id: str | None = None

    # operation_finished
    outcome: str | None = None
    error: JsonValue = None

    # step_attempt
    step: str | None = None
    attempt: int | None = None
    result_entry_id: str | None = None
    compaction_reason: str | None = None

    # tool_started
    assistant_entry_id: str | None = None
    tool_index: int | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    effective_args: JsonValue = None
    replay: str | None = None

    # queue_enqueued
    queue: str | None = None
    target: JsonValue = None

    # queue_cancelled
    entry_id: str | None = None

    # usage
    usage: JsonValue = None
    cause: str | None = None
    stop_reason: str | None = None


@dataclass
class LanePointer:
    lane: str
    leaf_id: str | None


@dataclass
class SessionStats:
    message_count: int = 0
    cached_tokens: int = 0
    uncached_tokens: int = 0
    total_tokens: int = 0
    cost_total: float = 0.0


@dataclass
class SessionMetadata:
    session_key: str
    parent_session_key: str | None = None
    created_at: int = 0


@dataclass
class EntryQuery:
    type: str | None = None
    custom_type: str | None = None
    order: EntryOrder = "newestFirst"
    limit: int | None = None
    after_seq: int | None = None
    # 分支扫描边界（find_entries_on_branch 使用）
    start: str | None = None
    stop_at_type: str | None = None
    stop_at_id: str | None = None


@dataclass
class RecordQuery:
    lane: str | None = None
    type: str | None = None
    run_id: str | None = None
    operation_kind: str | None = None
    after_seq: int | None = None
    order: EntryOrder = "newestFirst"
    limit: int | None = None


@dataclass
class LogItem:
    kind: str  # entry / record / lane / fact
    seq: int
    # 具体内容按 kind 不同：entry / record / lane+leaf_id / fact+name 或 target_id+label
    entry: Entry | None = None
    record: Record | None = None
    lane: str | None = None
    leaf_id: str | None = None
    fact: str | None = None
    name: str | None = None
    target_id: str | None = None
    label: str | None = None


@dataclass
class ForkOptions:
    scope: str = "branch"  # "branch" | "tree"
    entry_id: str | None = None
    # 默认值取决于是否显式指定 entry_id：指定时为 "before"，否则为 "at"。
    position: str | None = None


@dataclass
class CreateOptions:
    session_key: str | None = None
    parent_session_key: str | None = None


@dataclass
class CompactionSettings:
    enabled: bool = True
    reserve_tokens: int = 16384
    keep_recent_tokens: int = 20000


DEFAULT_COMPACTION_SETTINGS = CompactionSettings()
