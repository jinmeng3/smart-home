import json
from dataclasses import dataclass, field
from typing import Any

from app.agents.events.sse import encode_sse_event
from app.agents.redaction import redact_text
from app.agents.tools import WRITE_TOOL_NAMES
from app.schemas.sse import (
    ExecutionStatus,
    MessageDelta,
    ToolCompleted,
    ToolFailed,
    ToolStarted,
)


@dataclass
class StreamChunkResult:
    """``emit_stream_chunk`` 的返回结果（§5.3）。

    - ``events``: 应发送的 SSE 事件列表
    - ``tool_call_delta``: 本次新增的不同工具调用数（用于累计统计）
    - ``write_submit_names``: 本次新增的写工具名称列表（用于更新阶段状态）
    - ``write_result_failed``: 写工具节点返回的结果是否为失败
    """

    events: list[str] = field(default_factory=list)
    tool_call_delta: int = 0
    write_submit_names: list[str] = field(default_factory=list)
    write_result_failed: bool = False


class StreamTracker:
    def __init__(self, run_id: str, session_id: int):
        self.run_id = run_id
        self.session_id = session_id
        self.collected = ""
        self.seen_calls: set[str] = set()
        self.call_seq = 0
        self.exec_seq = 0

    def emit_tool_start(self, tool_call) -> str:
        tc = tool_call if isinstance(tool_call, dict) else tool_call.model_dump()
        tc_id = str(tc.get("id", ""))
        if tc_id and tc_id in self.seen_calls:
            return ""
        self.seen_calls.add(tc_id)
        self.call_seq += 1
        return encode_sse_event(
            ToolStarted(
                event_id=f"{self.run_id}-tool{self.call_seq}",
                run_id=self.run_id,
                call_id=tc_id or str(self.call_seq),
                tool=str(tc.get("name", "unknown")),
                summary=f"正在调用 {tc.get('name', 'unknown')}",
            )
        )

    def emit_tool_result(self, call_id: str, name: str, content):
        text = str(content)
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            payload = {"ok": True, "data": text}
        if payload.get("ok") is False:
            event: ToolCompleted | ToolFailed = ToolFailed(
                event_id=f"{self.run_id}-fail{self.call_seq}",
                run_id=self.run_id,
                call_id=call_id,
                tool=str(name),
                code="AGENT_TOOL_EXECUTION_ERROR",
                error=redact_text(str(payload.get("error", "工具执行失败")))[:500],
            )
        else:
            event = ToolCompleted(
                event_id=f"{self.run_id}-result{self.call_seq}",
                run_id=self.run_id,
                call_id=call_id,
                tool=str(name),
                result=redact_text(
                    json.dumps(payload.get("data"), ensure_ascii=False, default=str)
                )[:500],
            )
        return encode_sse_event(event)

    def emit_model_text(self, content: str):
        self.collected += str(content)
        return encode_sse_event(
            MessageDelta(
                event_id=f"{self.run_id}-{len(self.collected)}",
                run_id=self.run_id,
                content=str(content),
            )
        )

    def emit_execution_status(
        self,
        call_id: str,
        operator: str,
        status: str,
        message: str = "",
        execution_id: str | None = None,
    ) -> str:
        """发送写操作的执行状态事件（submitted/running/verified/failed）。"""
        self.exec_seq += 1
        return encode_sse_event(
            ExecutionStatus(
                event_id=f"{self.run_id}-exec{self.exec_seq}",
                run_id=self.run_id,
                session_id=self.session_id,
                operator=operator,
                status=status,
                call_id=call_id,
                execution_id=execution_id,
                message=message,
            )
        )

    def emit_execution_result(self, call_id: str, operator: str, content) -> str:
        """根据写工具节点返回的 ToolMessage 内容发送最终 execution_status。

        成功且 status 为 submitted（如场景异步执行）时发送 submitted；
        其余成功结果发送 verified；失败结果发送 failed。
        """
        text = str(content)
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            payload = {}

        if payload.get("ok") is False or payload.get("status") == "failed":
            return self.emit_execution_status(
                call_id=call_id,
                operator=operator,
                status="failed",
                message=redact_text(
                    str(payload.get("error", "写操作执行失败"))
                )[:500],
            )

        status = "submitted" if payload.get("status") == "submitted" else "verified"
        return self.emit_execution_status(
            call_id=call_id,
            operator=operator,
            status=status,
            message=redact_text(
                str(payload.get("message", "写操作执行完成"))
            )[:500],
            execution_id=(
                str(payload["execution_id"])
                if payload.get("execution_id")
                else None
            ),
        )

    def emit_stream_chunk(self, msg: Any, node: str) -> StreamChunkResult:
        """统一把一次流式消息转换为 SSE 事件列表（§5.3）。

        首次运行（runner）与审批恢复（resumer）复用同一事件转换器，
        避免两条路径的工具开始/结束事件不一致。

        副作用：
        - 对模型文本调用 ``emit_model_text`` 累加 ``self.collected``；
        - 对工具调用去重（``seen_calls``），返回本轮新增的调用数；
        - 对写工具节点结果解析失败状态。
        """
        result = StreamChunkResult()

        for tool_call in getattr(msg, "tool_calls", None) or []:
            tc = tool_call if isinstance(tool_call, dict) else tool_call.model_dump()
            tc_name = str(tc.get("name", ""))
            sse = self.emit_tool_start(tool_call)
            if sse:
                result.events.append(sse)
                result.tool_call_delta += 1
                if tc_name in WRITE_TOOL_NAMES:
                    result.write_submit_names.append(tc_name)

        name = getattr(msg, "name", None)
        content = getattr(msg, "content", None)
        if node in {"read_tool", "write_tool"} and name and content:
            call_id = str(getattr(msg, "tool_call_id", ""))
            result.events.append(self.emit_tool_result(call_id, name, content))
            if node == "write_tool":
                result.write_result_failed = self._is_write_result_failed(content)
                result.events.append(
                    self.emit_execution_result(call_id, name, content)
                )
        elif content and node == "model":
            result.events.append(self.emit_model_text(content))

        return result

    @staticmethod
    def _is_write_result_failed(content) -> bool:
        """判断写工具节点返回内容是否为失败结果。"""
        try:
            payload = json.loads(str(content))
        except (json.JSONDecodeError, TypeError):
            return False
        return payload.get("ok") is False or payload.get("status") == "failed"
