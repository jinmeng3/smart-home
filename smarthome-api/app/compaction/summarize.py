"""摘要请求的 LLM 调用封装（对应文档 §5.3 / §7.4）。

- ``complete_summarization``：统一的路由隔离 + 重试封装。每个摘要请求使用全新
  的 isolation id（等价于文档中的新 ``sessionId`` + 不写缓存），避免一次性提示词
  污染会话路由；瞬时错误按重试次数重试，取消 / 确定性错误立即抛出。
- ``langchain_summarizer``：把 langchain 模型适配为 ``Summarizer`` 协议，并标准
  化 ``usage_metadata``。

核心与具体模型供应商解耦：``Summarizer`` 是一个普通可调用对象，测试时可传入
假的摘要函数，无需真实的 LLM。
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import uuid4


class SummarizationAborted(Exception):
    """摘要被取消（用户中断 / abort 信号）。"""


class Summarizer(Protocol):
    """摘要请求的可调用协议。

    接收 system / user 两段提示词，返回 ``(文本, usage 或 None)``。``max_tokens``
    为本次请求的响应预算上限，``isolation_id`` 用于路由隔离与可观测性。
    """

    def __call__(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        isolation_id: str | None = None,
    ) -> tuple[str, dict[str, Any] | None]: ...


def complete_summarization(
    summarizer: Summarizer,
    system: str,
    user: str,
    *,
    max_tokens: int | None = None,
    retry_attempts: int = 0,
    isolation_id: str | None = None,
    is_aborted=None,
) -> tuple[str, dict[str, Any] | None]:
    """执行一次摘要请求，带路由隔离与重试。

    - ``retry_attempts``：瞬时错误的最大重试次数（总共最多尝试 N+1 次）。
    - ``is_aborted``：可选的可调用对象，返回 ``True`` 时立即抛出
      :class:`SummarizationAborted`（用于协作式取消）。
    """
    isolation_id = isolation_id or uuid4().hex
    attempts = 0
    while True:
        if is_aborted is not None and is_aborted():
            raise SummarizationAborted("Summarization aborted")
        try:
            return summarizer(
                system, user, max_tokens=max_tokens, isolation_id=isolation_id
            )
        except SummarizationAborted:
            raise
        except Exception:
            if attempts >= retry_attempts:
                raise
            attempts += 1


def langchain_summarizer(model) -> Summarizer:
    """把 langchain ``BaseChatModel`` 适配为 :class:`Summarizer`。"""

    def _summarize(
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        isolation_id: str | None = None,
    ) -> tuple[str, dict[str, Any] | None]:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        if max_tokens is not None:
            response = model.invoke(messages, max_tokens=max_tokens)
        else:
            response = model.invoke(messages)

        content = getattr(response, "content", None)
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(block.get("text", "") or "")
                else:
                    parts.append(str(block))
            content = "".join(parts)

        from app.compaction.usage import usage_from_metadata as _usage_impl

        usage = _usage_impl(getattr(response, "usage_metadata", None))
        return str(content or ""), usage

    return _summarize
