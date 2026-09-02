"""上下文压缩与分支摘要的编排层（对应文档 §2 / §5 / §7）。

这是 ``session_tree`` 纯逻辑的"上层集成点"：负责触发判定、调用 LLM 生成摘要、
把 ``CompactionEntry`` / ``BranchSummaryEntry`` 追加回会话树并重建上下文。

与 ``session_tree`` 的分工：
- ``session_tree.compaction`` 只做无副作用的纯计算（切割点、token 估算、准备）。
- 本模块持有摘要器（LLM）、扩展钩子，执行实际摘要请求与落盘。

摘要器通过 :class:`~app.compaction.summarize.Summarizer` 协议注入，与具体模型
供应商解耦；测试时可传入假的摘要函数，无需真实 LLM。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.compaction.events import (
    AfterBranchSummaryEvent,
    AfterCompactEvent,
    BeforeBranchSummaryEvent,
    BeforeCompactEvent,
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
from app.compaction.serialize import serialize_conversation
from app.compaction.summarize import (
    SummarizationAborted,
    Summarizer,
    complete_summarization,
)
from app.compaction.usage import combine_usage
from app.session_tree.compaction.branch_summary import (
    collect_entries_for_branch_summary,
    prepare_branch_entries,
)
from app.session_tree.compaction.compaction import (
    compute_file_lists,
    estimate_context_tokens,
    format_file_operations,
    prepare_compaction,
    should_compact,
)
from app.session_tree.session.context import build_session_context
from app.session_tree.session.storage import Session
from app.session_tree.session.types import (
    CompactionSettings,
    Entry,
    EntryQuery,
)


@dataclass
class CompactionDecision:
    """压缩触发判定结果（对应文档 §2 的跳过规则）。"""

    should_compact: bool
    reason: str  # "threshold" | "disabled" | "already_compacted" | "nothing_to_compact" | "aborted" | "ok"
    context_tokens: int
    context_window: int
    reserve_tokens: int
    keep_recent_tokens: int


@dataclass
class CompactionResult:
    summary: str
    tokens_before: int
    estimated_tokens_after: int
    entry_id: str | None
    usage: dict[str, Any] | None
    is_split_turn: bool
    reason: str
    will_retry: bool
    aborted: bool = False


@dataclass
class BranchSummaryResult:
    summary: str
    usage: dict[str, Any] | None = None
    entry_id: str | None = None
    read_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    aborted: bool = False


def _details_to_lists(details: Any) -> tuple[list[str], list[str]]:
    """从扩展提供的 details 中解析 readFiles / modifiedFiles。"""
    if not isinstance(details, dict):
        return [], []
    read_files = details.get("readFiles") or []
    modified_files = details.get("modifiedFiles") or []
    return (
        [path for path in read_files if isinstance(path, str)],
        [path for path in modified_files if isinstance(path, str)],
    )


def _compute_file_lists(file_ops: Any) -> tuple[list[str], list[str]]:
    """把 ``FileOperations`` 转为 ``(read_files, modified_files)`` 元组。"""
    lists = compute_file_lists(file_ops)
    return lists["readFiles"], lists["modifiedFiles"]


class CompactionEngine:
    """上下文压缩 / 分支摘要的编排入口。

    对应文档中的 ``AgentSession`` 编排层：``evaluate`` 判定是否压缩，``compact``
    执行压缩，``summarize_branch`` 执行分支摘要。
    """

    def __init__(
        self,
        summarizer: Summarizer,
        *,
        id_factory: Any | None = None,
        hooks: CompactionHooks | None = None,
        retry_attempts: int | None = None,
        max_tokens: int | None = None,
        is_aborted: Any | None = None,
        branch_summary_max_tokens: int | None = None,
        tool_result_max_chars: int | None = None,
    ) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        self._summarizer = summarizer
        self._id_factory = id_factory or (lambda: uuid4().hex)
        self._hooks = hooks or CompactionHooks()
        # 传参为空时回退到 ``.env`` 配置，保持与显式传参一致的语义。
        self._retry_attempts = (
            settings.compaction_retry_attempts
            if retry_attempts is None
            else retry_attempts
        )
        # 模型的最大完成 token 数（用于给摘要响应预算设上限，None 表示不设上限）。
        self._max_tokens = (
            settings.compaction_max_tokens if max_tokens is None else max_tokens
        )
        self._branch_summary_max_tokens = (
            settings.compaction_branch_summary_max_tokens
            if branch_summary_max_tokens is None
            else branch_summary_max_tokens
        )
        self._tool_result_max_chars = (
            settings.compaction_tool_result_max_chars
            if tool_result_max_chars is None
            else tool_result_max_chars
        )
        # 协作式取消探测：返回 True 时在下次摘要请求前抛出 SummarizationAborted。
        self._is_aborted = is_aborted

    def _resolve_settings(
        self, settings: CompactionSettings | None
    ) -> CompactionSettings:
        """解析压缩配置：显式传参优先，否则回退到 ``.env`` 配置。"""
        if settings is not None:
            return settings
        from app.core.config import get_settings

        return get_settings().compaction_settings()

    # === 触发判定 ===

    def evaluate(
        self,
        session: Session,
        *,
        context_window: int,
        settings: CompactionSettings | None = None,
        last_assistant_message: dict[str, Any] | None = None,
        lane: str = "main",
    ) -> CompactionDecision:
        """判定当前会话是否需要压缩，返回决策与原因。

        实现了文档 §2.4 中可在树内确定的跳过规则；依赖 agent 运行时状态（模型
        切换、usage 早于压缩边界等）的规则由调用方自行处理。
        """
        settings = self._resolve_settings(settings)
        path = self._path_entries(session, lane)
        messages = build_session_context(path)["messages"]

        def decision(reason: str, tokens: int) -> CompactionDecision:
            return CompactionDecision(
                should_compact=(reason == "threshold"),
                reason=reason,
                context_tokens=tokens,
                context_window=context_window,
                reserve_tokens=settings.reserve_tokens,
                keep_recent_tokens=settings.keep_recent_tokens,
            )

        if not settings.enabled:
            return decision("disabled", 0)
        if path and path[-1].type == "compaction":
            return decision("already_compacted", 0)
        if not messages:
            return decision("nothing_to_compact", 0)
        if (
            last_assistant_message is not None
            and last_assistant_message.get("stopReason") == "aborted"
        ):
            return decision("aborted", 0)

        tokens = estimate_context_tokens(messages)["tokens"]
        if should_compact(tokens, context_window, settings):
            return decision("threshold", tokens)
        return decision("ok", tokens)

    # === 压缩 ===

    def compact(
        self,
        session: Session,
        *,
        settings: CompactionSettings | None = None,
        custom_instructions: str | None = None,
        reason: str = "manual",
        will_retry: bool = False,
        lane: str = "main",
    ) -> CompactionResult:
        """执行一次压缩：生成摘要并追加 ``CompactionEntry``，重建上下文。

        ``reason`` 取值 ``"manual" | "threshold" | "overflow"``；``will_retry``
        用于溢出恢复（压缩后由调用方决定是否自动重试一次）。
        """
        settings = self._resolve_settings(settings)
        path = self._path_entries(session, lane)
        preparation = prepare_compaction(path, settings)

        if preparation is None or not (
            preparation.messages_to_summarize or preparation.turn_prefix_messages
        ):
            event = AfterCompactEvent(
                reason="nothing_to_compact",
                will_retry=will_retry,
                entry_id=None,
                summary="",
                tokens_before=0,
                estimated_tokens_after=0,
            )
            self._notify_after_compact(event)
            return CompactionResult(
                summary="",
                tokens_before=0,
                estimated_tokens_after=0,
                entry_id=None,
                usage=None,
                is_split_turn=False,
                reason="nothing_to_compact",
                will_retry=will_retry,
            )

        before = BeforeCompactEvent(
            reason=reason,
            will_retry=will_retry,
            preparation=preparation,
            custom_instructions=custom_instructions,
        )
        override = self._run_before_compact_hooks(before)
        if override is not None and override.cancel:
            return self._aborted_compact_result(preparation, reason, will_retry)

        try:
            if override is not None and override.summary is not None:
                summary_text = override.summary
                usage = override.usage
                read_files, modified_files = _details_to_lists(override.details)
            else:
                summary_text, usage = self._generate_summary(
                    preparation, settings, custom_instructions
                )
                read_files, modified_files = _compute_file_lists(preparation.file_ops)
                summary_text = summary_text.rstrip() + format_file_operations(
                    read_files, modified_files
                )
        except SummarizationAborted:
            return self._aborted_compact_result(preparation, reason, will_retry)

        details = (
            override.details
            if override is not None and override.details is not None
            else {"readFiles": read_files, "modifiedFiles": modified_files}
        )

        entry = Entry(
            type="compaction",
            id=self._id_factory(),
            summary=summary_text,
            retained_tail=preparation.retained_tail,
            tokens_before=preparation.tokens_before,
            details=details,
            usage=usage,
        )
        appended = session.append_entry(entry, lane)

        rebuilt = build_session_context(self._path_entries(session, lane))
        estimated_after = estimate_context_tokens(rebuilt["messages"])["tokens"]

        event = AfterCompactEvent(
            reason=reason,
            will_retry=will_retry,
            entry_id=appended.id,
            summary=summary_text,
            tokens_before=preparation.tokens_before,
            estimated_tokens_after=estimated_after,
        )
        self._notify_after_compact(event)

        return CompactionResult(
            summary=summary_text,
            tokens_before=preparation.tokens_before,
            estimated_tokens_after=estimated_after,
            entry_id=appended.id,
            usage=usage,
            is_split_turn=preparation.is_split_turn,
            reason=reason,
            will_retry=will_retry,
        )

    # === 分支摘要 ===

    def generate_branch_summary(
        self,
        session: Session,
        *,
        old_leaf_id: str | None,
        target_id: str,
        context_window: int,
        settings: CompactionSettings | None = None,
        custom_instructions: str | None = None,
        replace_instructions: bool = False,
    ) -> BranchSummaryResult:
        """仅生成分支摘要文本（不追加条目），供扩展钩子复用。"""
        settings = self._resolve_settings(settings)
        collected = collect_entries_for_branch_summary(session, old_leaf_id, target_id)
        if not collected.entries:
            return BranchSummaryResult(summary="")

        budget = context_window - settings.reserve_tokens
        preparation = prepare_branch_entries(collected.entries, budget)
        if not preparation.messages:
            return BranchSummaryResult(summary="")

        base_prompt = BRANCH_SUMMARY_PROMPT
        if replace_instructions and custom_instructions:
            base_prompt = custom_instructions
        elif custom_instructions:
            base_prompt += f"\n\nAdditional focus: {custom_instructions}"

        conversation = serialize_conversation(
            preparation.messages, tool_result_max_chars=self._tool_result_max_chars
        )
        prompt = f"<conversation>\n{conversation}\n</conversation>\n\n{base_prompt}"
        text, usage = complete_summarization(
            self._summarizer,
            SUMMARIZATION_SYSTEM_PROMPT,
            prompt,
            max_tokens=self._branch_summary_max_tokens,
            retry_attempts=self._retry_attempts,
            is_aborted=self._is_aborted,
        )

        read_files, modified_files = _compute_file_lists(preparation.file_ops)
        text = (
            BRANCH_SUMMARY_PREAMBLE
            + "\n\n"
            + text.rstrip()
            + format_file_operations(read_files, modified_files)
        )
        return BranchSummaryResult(
            summary=text,
            usage=usage,
            read_files=read_files,
            modified_files=modified_files,
        )

    def summarize_branch(
        self,
        session: Session,
        *,
        old_leaf_id: str | None,
        target_id: str,
        context_window: int,
        settings: CompactionSettings | None = None,
        custom_instructions: str | None = None,
        replace_instructions: bool = False,
        lane: str = "main",
    ) -> BranchSummaryResult:
        """执行分支摘要：把被抛弃分支压缩成摘要，挂到导航目标之后。

        对应文档 §7.5：先 ``move_lane`` 到目标节点，再把 ``BranchSummaryEntry``
        追加到目标处（叶子落在 user 消息 parent 等细节由调用方处理）。
        """
        settings = self._resolve_settings(settings)
        collected = collect_entries_for_branch_summary(session, old_leaf_id, target_id)

        before = BeforeBranchSummaryEvent(
            old_leaf_id=old_leaf_id,
            target_id=target_id,
            user_wants_summary=True,
            entries_to_summarize=collected.entries,
        )
        override = self._run_before_branch_summary_hooks(before)
        if override is not None and override.cancel:
            return BranchSummaryResult(summary="", aborted=True)

        try:
            if override is not None and override.summary is not None:
                summary_text = override.summary
                usage = override.usage
                read_files, modified_files = _details_to_lists(override.details)
            else:
                draft = self.generate_branch_summary(
                    session,
                    old_leaf_id=old_leaf_id,
                    target_id=target_id,
                    context_window=context_window,
                    settings=settings,
                    custom_instructions=custom_instructions,
                    replace_instructions=replace_instructions,
                )
                if not draft.summary:
                    return BranchSummaryResult(summary="")
                summary_text = draft.summary
                usage = draft.usage
                read_files, modified_files = draft.read_files, draft.modified_files
        except SummarizationAborted:
            return BranchSummaryResult(summary="", aborted=True)

        details = (
            override.details
            if override is not None and override.details is not None
            else {"readFiles": read_files, "modifiedFiles": modified_files}
        )

        session.move_lane(lane, target_id)
        entry = Entry(
            type="branch_summary",
            id=self._id_factory(),
            from_id=old_leaf_id,
            summary=summary_text,
            details=details,
            usage=usage,
        )
        appended = session.append_entry(entry, lane)

        self._notify_after_branch_summary(
            AfterBranchSummaryEvent(
                old_leaf_id=old_leaf_id,
                target_id=target_id,
                entry_id=appended.id,
            )
        )
        return BranchSummaryResult(
            summary=summary_text,
            usage=usage,
            entry_id=appended.id,
            read_files=read_files,
            modified_files=modified_files,
        )

    # === 内部：摘要生成 ===

    def _generate_summary(
        self,
        preparation,
        settings: CompactionSettings,
        custom_instructions: str | None,
    ) -> tuple[str, dict[str, Any] | None]:
        reserve = settings.reserve_tokens
        if not preparation.is_split_turn:
            return self._summarize_messages(
                preparation.messages_to_summarize,
                previous_summary=preparation.previous_summary,
                custom_instructions=custom_instructions,
                max_tokens=self._budget(reserve, 0.8),
            )

        history_text, history_usage = ("", None)
        if preparation.messages_to_summarize:
            history_text, history_usage = self._summarize_messages(
                preparation.messages_to_summarize,
                previous_summary=preparation.previous_summary,
                custom_instructions=custom_instructions,
                max_tokens=self._budget(reserve, 0.8),
            )
        prefix_text, prefix_usage = self._summarize_turn_prefix(
            preparation.turn_prefix_messages,
            max_tokens=self._budget(reserve, 0.5),
        )

        if history_text:
            combined = (
                history_text
                + "\n\n---\n\n**Turn Context (split turn):**\n\n"
                + prefix_text
            )
        else:
            combined = prefix_text
        return combined, combine_usage(history_usage, prefix_usage)

    def _summarize_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        previous_summary: str | None,
        custom_instructions: str | None,
        max_tokens: int,
    ) -> tuple[str, dict[str, Any] | None]:
        conversation = serialize_conversation(
            messages, tool_result_max_chars=self._tool_result_max_chars
        )
        base_prompt = (
            UPDATE_SUMMARIZATION_PROMPT if previous_summary else SUMMARIZATION_PROMPT
        )
        if custom_instructions:
            base_prompt += f"\n\nAdditional focus: {custom_instructions}"

        prompt = f"<conversation>\n{conversation}\n</conversation>\n\n"
        if previous_summary:
            prompt += f"<previous-summary>\n{previous_summary}\n</previous-summary>\n\n"
        prompt += base_prompt

        return complete_summarization(
            self._summarizer,
            SUMMARIZATION_SYSTEM_PROMPT,
            prompt,
            max_tokens=max_tokens,
            retry_attempts=self._retry_attempts,
            is_aborted=self._is_aborted,
        )

    def _summarize_turn_prefix(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int,
    ) -> tuple[str, dict[str, Any] | None]:
        conversation = serialize_conversation(
            messages, tool_result_max_chars=self._tool_result_max_chars
        )
        prompt = (
            f"<conversation>\n{conversation}\n</conversation>\n\n"
            + TURN_PREFIX_SUMMARIZATION_PROMPT
        )
        return complete_summarization(
            self._summarizer,
            SUMMARIZATION_SYSTEM_PROMPT,
            prompt,
            max_tokens=max_tokens,
            retry_attempts=self._retry_attempts,
            is_aborted=self._is_aborted,
        )

    def _budget(self, reserve: int, factor: float) -> int:
        budget = math.floor(factor * reserve)
        if self._max_tokens and self._max_tokens > 0:
            return min(budget, self._max_tokens)
        return budget

    # === 内部：路径 / 钩子 / 结果 ===

    def _path_entries(self, session: Session, lane: str) -> list[Entry]:
        view = session.view(lane)
        leaf = view.get_leaf_id()
        if leaf is None:
            return []
        return view.find_entries_on_branch(EntryQuery(start=leaf, order="oldestFirst"))

    def _run_before_compact_hooks(self, event: BeforeCompactEvent):
        for hook in self._hooks.before_compact:
            result = hook(event)
            if result is not None:
                return result
        return None

    def _run_before_branch_summary_hooks(self, event: BeforeBranchSummaryEvent):
        for hook in self._hooks.before_branch_summary:
            result = hook(event)
            if result is not None:
                return result
        return None

    def _notify_after_compact(self, event: AfterCompactEvent) -> None:
        for hook in self._hooks.after_compact:
            hook(event)

    def _notify_after_branch_summary(self, event: AfterBranchSummaryEvent) -> None:
        for hook in self._hooks.after_branch_summary:
            hook(event)

    def _aborted_compact_result(
        self, preparation, reason: str, will_retry: bool
    ) -> CompactionResult:
        event = AfterCompactEvent(
            reason=reason,
            will_retry=will_retry,
            entry_id=None,
            summary="",
            tokens_before=preparation.tokens_before,
            estimated_tokens_after=preparation.tokens_before,
            aborted=True,
        )
        self._notify_after_compact(event)
        return CompactionResult(
            summary="",
            tokens_before=preparation.tokens_before,
            estimated_tokens_after=preparation.tokens_before,
            entry_id=None,
            usage=None,
            is_split_turn=preparation.is_split_turn,
            reason=reason,
            will_retry=will_retry,
            aborted=True,
        )
