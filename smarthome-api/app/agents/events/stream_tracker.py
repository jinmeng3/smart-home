import json

from app.agents.events.sse import encode_sse_event
from app.agents.redaction import redact_text
from app.schemas.sse import (
    MessageDelta,
    ToolCompleted,
    ToolFailed,
    ToolStarted,
)


class StreamTracker:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.collected = ""
        self.seen_calls: set[str] = set()
        self.call_seq = 0

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
