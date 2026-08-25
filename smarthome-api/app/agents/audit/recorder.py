import json
import typing
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
        self._current_bucket: str | None = None
        self._current_file: typing.IO | None = None

    def _write(self, entry: dict) -> None:
        """
        将审计记录追加到当前小时桶的 .json 文件。
        每个小时一个文件，避免单次写入产生大量小文件，
        同一个桶内复用文件句柄，不重复 open/close。
        文件名示例：audit_20260418_14.json
        """
        bucket = datetime.now(timezone.utc).strftime("%Y%m%d_%H")
        line = json.dumps(entry, ensure_ascii=False, default=str)
        if bucket != self._current_bucket:
            if self._current_file is not None:
                self._current_file.close()
            self._current_file = open(  # noqa: SIM115  # 故意长期持有句柄以复用小时桶文件，见方法 docstring
                self.log_dir / f"audit_{bucket}.json", "a", encoding="utf-8"
            )
            self._current_bucket = bucket
                                               
        assert self._current_file is not None
        self._current_file.write(line + "\n")
        self._current_file.flush()

    def record_run_start(self, context: AgentContext, run_id: str) -> None:
        entry = {
            "event": "run_start",
            "run_id": run_id,
            "user_id": context.user_id,
            "household_id": context.household_id,
            "session_id": context.session_id,
            "auto_execute_low_risk": context.auto_execute_low_risk,
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

    def record_approval_required(
        self,
        *,
        run_id: str,
        approval_id: str,
        tool: str,
        risk_level: str,
        reasons: list[str],
    ) -> None:
        entry = {
            "event": "approval_required",
            "run_id": run_id,
            "approval_id": approval_id,
            "tool": tool,
            "risk_level": risk_level,
            "reasons": reasons,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_approval_decision(
        self,
        *,
        run_id: str,
        approval_id: str,
        decision: str,
        automatic: bool = False,
    ) -> None:
        entry = {
            "event": "approval_decision",
            "run_id": run_id,
            "approval_id": approval_id,
            "decision": decision,
            "automatic": automatic,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_subagent_start(self, *, run_id: str, domain: str, task: str) -> None:
        """记录一次子 Agent 运行的开始边界。"""
        entry = {
            "event": "subagent_start",
            "run_id": run_id,
            "domain": domain,
            "task": redact_text(task)[:500],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_subagent_end(
        self,
        *,
        run_id: str,
        domain: str,
        status: str,
        summary: str = "",
        duration_ms: int | None = None,
        usage: dict | None = None,
    ) -> None:
        """记录一次子 Agent 运行的结束边界。"""
        entry = {
            "event": "subagent_end",
            "run_id": run_id,
            "domain": domain,
            "status": status,
            "summary": redact_text(summary)[:500],
            "duration_ms": duration_ms,
            "usage": usage or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def record_run_replay(
        self,
        *,
        run_id: str,
        context: AgentContext,
        messages: list[dict],
        model_name: str,
        tool_calls: list[dict],
        approvals: list[dict],
        status: str,
        duration_ms: int,
    ) -> None:
        """记录完整的运行回放数据，用于事后审计和问题排查。"""
        entry = {
            "event": "run_replay",
            "run_id": run_id,
            "user_id": context.user_id,
            "household_id": context.household_id,
            "session_id": context.session_id,
            "model_name": model_name,
            "status": status,
            "duration_ms": duration_ms,
            "messages": [
                {
                    "role": m.get("role", "unknown"),
                    "content": redact_text(str(m.get("content", "")))[:1000],
                    "tool_calls": [
                        {
                            "name": tc.get("name", ""),
                            "args": redact_fields(tc.get("args", {})),
                        }
                        for tc in (m.get("tool_calls") or [])
                    ]
                    if m.get("tool_calls")
                    else None,
                }
                for m in messages
            ],
            "tool_calls": [
                {
                    "call_id": tc.get("call_id"),
                    "tool": tc.get("tool"),
                    "args": redact_fields(tc.get("args", {})),
                    "ok": tc.get("ok"),
                }
                for tc in tool_calls
            ],
            "approvals": redact_fields({"items": approvals})["items"],
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self._write(entry)

    def close(self) -> None:
        """关闭当前小时桶文件句柄（下一次写入会自动重开）。"""
        if self._current_file is not None:
            self._current_file.close()
            self._current_file = None
            self._current_bucket = None


_audit: AuditRecorder | None = None


def get_audit_recorder() -> AuditRecorder:
    global _audit
    if _audit is None:
        _audit = AuditRecorder()
    return _audit
