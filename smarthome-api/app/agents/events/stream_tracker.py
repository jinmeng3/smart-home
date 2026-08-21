import json

from app.agents.events.sse import encode_sse_event
from app.agents.redaction import redact_text
from app.schemas.sse import (
    ExecutionStatus,
    MessageDelta,
    ToolCompleted,
    ToolFailed,
    ToolStarted,
)


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
