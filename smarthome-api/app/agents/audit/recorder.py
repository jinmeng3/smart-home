import json
import threading
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
        # 进程内同步：文件切换与写入共用一个锁，避免并发写交错（§6.3）
        self._lock = threading.Lock()

    def _write(self, entry: dict) -> None:
        """
        将审计记录追加到当前小时桶的 .json 文件。
        每个小时一个文件，避免单次写入产生大量小文件，
        同一个桶内复用文件句柄，不重复 open/close。
        文件名示例：audit_20260418_14.json
        """
        bucket = datetime.now(timezone.utc).strftime("%Y%m%d_%H")
        line = json.dumps(entry, ensure_ascii=False, default=str)
        with self._lock:
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
        approval_id: str | None = None,
        approval_decision: str | None = None,
        automatic: bool | None = None,
        error_code: str | None = None,
    ) -> None:
        """记录（含写工具的）一次工具调用结果。

        写工具调用还携带：审批 ID、审批决定（approve/reject/auto）、
        是否自动批准、错误码，用于按 ``run_id`` 串联完整审计链（§4.5）。
        """
        entry = {
            "event": "tool_completed" if ok else "tool_failed",
            "run_id": run_id,
            "call_id": call_id,
            "tool": tool,
            "args": redact_fields(args),
            "result": redact_text(str(result))[:2000],
            "duration_ms": duration_ms,
            "approval_id": approval_id,
            "approval_decision": approval_decision,
            "automatic": automatic,
            "error_code": error_code,
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


    def close(self) -> None:
        """关闭当前小时桶文件句柄（下一次写入会自动重开）。"""
        with self._lock:
            if self._current_file is not None:
                try:
                    self._current_file.close()
                finally:
                    self._current_file = None
                    self._current_bucket = None


_audit: AuditRecorder | None = None


def get_audit_recorder() -> AuditRecorder:
    global _audit
    if _audit is None:
        _audit = AuditRecorder()
    return _audit
