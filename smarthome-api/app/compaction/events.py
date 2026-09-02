"""压缩与分支摘要的事件与扩展钩子（对应文档 §10）。

钩子均为可调用对象：返回 ``None`` 表示不干预；返回对应 Result 可取消操作或
提供自定义摘要（如换成自己的模型总结）。这样扩展可以完全接管摘要逻辑，而
默认路径保持不变。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.session_tree.compaction import CompactionPreparation

# === 压缩事件 ===


@dataclass
class BeforeCompactEvent:
    reason: str  # "manual" | "threshold" | "overflow"
    will_retry: bool  # 溢出恢复时压缩后是否自动重试一次
    preparation: CompactionPreparation
    custom_instructions: str | None = None


@dataclass
class BeforeCompactResult:
    """返回 ``cancel=True`` 取消压缩；返回 ``summary`` 接管摘要生成。"""

    cancel: bool = False
    summary: str | None = None
    usage: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


@dataclass
class AfterCompactEvent:
    reason: str
    will_retry: bool
    entry_id: str | None
    summary: str
    tokens_before: int
    estimated_tokens_after: int
    aborted: bool = False


# === 分支摘要事件 ===


@dataclass
class BeforeBranchSummaryEvent:
    old_leaf_id: str | None
    target_id: str
    user_wants_summary: bool
    entries_to_summarize: list[Any] = field(default_factory=list)


@dataclass
class BeforeBranchSummaryResult:
    cancel: bool = False
    summary: str | None = None
    usage: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


@dataclass
class AfterBranchSummaryEvent:
    old_leaf_id: str | None
    target_id: str
    entry_id: str | None


# === 钩子类型 ===


BeforeCompactHook = Callable[[BeforeCompactEvent], BeforeCompactResult | None]
AfterCompactHook = Callable[[AfterCompactEvent], None]
BeforeBranchSummaryHook = Callable[
    [BeforeBranchSummaryEvent], BeforeBranchSummaryResult | None
]
AfterBranchSummaryHook = Callable[[AfterBranchSummaryEvent], None]


@dataclass
class CompactionHooks:
    """捆绑四个扩展钩子；默认全为空列表（不干预默认路径）。"""

    before_compact: list[BeforeCompactHook] = field(default_factory=list)
    after_compact: list[AfterCompactHook] = field(default_factory=list)
    before_branch_summary: list[BeforeBranchSummaryHook] = field(default_factory=list)
    after_branch_summary: list[AfterBranchSummaryHook] = field(default_factory=list)
