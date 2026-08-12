import json
from datetime import datetime, timezone
from pathlib import Path

from app.agents.context import AgentContext
from app.agents.redaction import redact_fields, redact_text
from app.core.config import get_settings

DEFAULT_AUDIT_DIR = get_settings().audit_path


class AuditRecorder:
    def __init__(self, log_dir: str | Path = DEFAULT_AUDIT_DIR):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _write(self, entry: dict) -> None:
        time_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        line = json.dumps(entry, ensure_ascii=False, default=str)
        with open(self.log_dir / f"{time_stamp}.json", "w", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_run_start(self, context: AgentContext, run_id: str) -> None:
        entry = {
            "event": "run_start",
            "run_id": run_id,
            "user_id": context.user_id,
            "household_id": context.household_id,
            "session_id": context.session_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_run_end(
        self, run_id: str, status: str = "completed", message: str = ""
    ) -> None:
        entry = {
            "event": "run_end",
            "run_id": run_id,
            "status": status,
            "message": redact_text(message)[:200],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_tool_call(
        self,
        *,
        run_id,
        call_id,
        tool,
        args,
        result,
        ok: bool = True,
        duration_ms: int | None = None,
    ) -> None:
        entry = {
            "event": "tool_completed" if ok else "tool_failed",
            "run_id": run_id,
            "call_id": call_id,
            "tool": tool,
            "args": redact_fields(args),
            "result": redact_text(str(result))[:2000],
            "duration_ms": duration_ms,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)


_audit: AuditRecorder | None = None


def get_audit_recorder() -> AuditRecorder:
    global _audit
    if _audit is None:
        _audit = AuditRecorder()
    return _audit
