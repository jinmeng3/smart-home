from app.agents.events.models import (
    MessageDelta,
    ToolCompleted,
    ToolFailed,
    ToolStarted,
)
from app.agents.events.sse import encode_sse_event
from app.agents.redaction import redact_text


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
        from app.core.config import get_settings

        error_prefix = get_settings().tool_error_prefix or "[tool_error] "
        text = str(content)
        if text.startswith(error_prefix):
            event: ToolCompleted | ToolFailed = ToolFailed(
                event_id=f"{self.run_id}-fail{self.call_seq}",
                run_id=self.run_id,
                call_id=call_id,
                tool=str(name),
                code="AGENT_TOOL_EXECUTION_ERROR",
                error=redact_text(text[len(error_prefix) :])[:500],
            )
        else:
            event = ToolCompleted(
                event_id=f"{self.run_id}-result{self.call_seq}",
                run_id=self.run_id,
                call_id=call_id,
                tool=str(name),
                result=redact_text(text)[:500],
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
