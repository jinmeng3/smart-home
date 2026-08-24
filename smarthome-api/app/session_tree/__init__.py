"""Pi 会话存储树形结构的 Python + SQLite 实现。

目录结构（对应文档结构）：

- ``session/``：类型、状态机、门面、内存 / SQLite 存储与仓库、上下文投影、编解码
- ``compaction/``：压缩与分支摘要纯逻辑
- ``errors.py``：``SessionError``
- ``messages.py``：消息辅助函数

顶层包作为聚合门面，统一导出上述子模块的公共 API。
"""

from app.session_tree.compaction import (
    BranchPreparation,
    CollectEntriesResult,
    CompactionPreparation,
    CutPointResult,
    FileOperations,
    collect_entries_for_branch_summary,
    estimate_tokens,
    find_cut_point,
    prepare_branch_entries,
    prepare_compaction,
    should_compact,
)
from app.session_tree.errors import SessionError
from app.session_tree.session import (
    CompactionSettings,
    CreateOptions,
    Entry,
    EntryQuery,
    ForkOptions,
    InMemorySessionRepo,
    InMemorySessionStorage,
    LanePointer,
    LogItem,
    Record,
    RecordQuery,
    Session,
    SessionMetadata,
    SessionState,
    SessionStats,
    SqliteSessionRepo,
    SqliteSessionStorage,
    build_session_context,
)

__all__ = [
    "BranchPreparation",
    "CollectEntriesResult",
    "CompactionPreparation",
    "CompactionSettings",
    "CreateOptions",
    "CutPointResult",
    "Entry",
    "EntryQuery",
    "FileOperations",
    "ForkOptions",
    "InMemorySessionRepo",
    "InMemorySessionStorage",
    "LanePointer",
    "LogItem",
    "Record",
    "RecordQuery",
    "Session",
    "SessionError",
    "SessionMetadata",
    "SessionState",
    "SessionStats",
    "SqliteSessionRepo",
    "SqliteSessionStorage",
    "build_session_context",
    "collect_entries_for_branch_summary",
    "estimate_tokens",
    "find_cut_point",
    "prepare_branch_entries",
    "prepare_compaction",
    "should_compact",
]
