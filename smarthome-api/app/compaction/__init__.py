"""上下文压缩与分支摘要的编排层（LLM 摘要生成 + 触发判定）。

- ``engine``：``CompactionEngine``（对应文档的 ``AgentSession`` 编排层）
- ``summarize``：摘要请求封装（路由隔离、重试、langchain 适配）
- ``serialize``：会话消息序列化
- ``prompts``：压缩 / 分支摘要 / 迭代更新的提示词
- ``usage``：usage 合并与标准化
- ``events``：扩展钩子与事件

纯逻辑（切割点、token 估算、``prepare_compaction`` / ``prepare_branch_entries``）
位于 ``app.session_tree.compaction``，本包只负责上层集成。
"""

from app.compaction.engine import (
    BranchSummaryResult,
    CompactionDecision,
    CompactionEngine,
    CompactionResult,
)
from app.compaction.events import (
    AfterBranchSummaryEvent,
    AfterCompactEvent,
    BeforeBranchSummaryEvent,
    BeforeBranchSummaryResult,
    BeforeCompactEvent,
    BeforeCompactResult,
    CompactionHooks,
)
from app.compaction.prompts import (
    BRANCH_SUMMARY_PREAMBLE,
    BRANCH_SUMMARY_PROMPT,
    SUMMARIZATION_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    TURN_PREFIX_SUMMARIZATION_PROMPT,
    UPDATE_SUMMARIZATION_PROMPT,
)
from app.compaction.serialize import (
    TOOL_RESULT_MAX_CHARS,
    serialize_conversation,
    truncate_tool_result,
)
from app.compaction.summarize import (
    SummarizationAborted,
    Summarizer,
    complete_summarization,
    create_langchain_summarizer,
)
from app.compaction.usage import combine_usage, usage_from_metadata

__all__ = [
    "BRANCH_SUMMARY_PREAMBLE",
    "BRANCH_SUMMARY_PROMPT",
    "SUMMARIZATION_PROMPT",
    "SUMMARIZATION_SYSTEM_PROMPT",
    "TOOL_RESULT_MAX_CHARS",
    "TURN_PREFIX_SUMMARIZATION_PROMPT",
    "UPDATE_SUMMARIZATION_PROMPT",
    "AfterBranchSummaryEvent",
    "AfterCompactEvent",
    "BeforeBranchSummaryEvent",
    "BeforeBranchSummaryResult",
    "BeforeCompactEvent",
    "BeforeCompactResult",
    "BranchSummaryResult",
    "CompactionDecision",
    "CompactionEngine",
    "CompactionHooks",
    "CompactionResult",
    "SummarizationAborted",
    "Summarizer",
    "combine_usage",
    "complete_summarization",
    "create_langchain_summarizer",
    "serialize_conversation",
    "truncate_tool_result",
    "usage_from_metadata",
]
