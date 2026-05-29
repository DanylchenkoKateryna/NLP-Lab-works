"""
tool_logger.py — Structured logger for agent tool calls.

Records every call with: timestamp, task_id, tool_name, input,
output, success, error, reason.  Saves to JSON Lines (JSONL) format.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


class ToolCallLogger:
    """
    Records every tool call with full metadata.

    Usage
    -----
    logger = ToolCallLogger()

    # Option A — manual log
    result = my_tool(x=1)
    logger.log(task_id="t01", tool_name="my_tool",
               input_data={"x": 1}, output_data=result,
               success=True, reason="why this tool")

    # Option B — auto call + log
    output, entry = logger.call(
        task_id="t01", tool_name="my_tool",
        tool_fn=my_tool, input_data={"x": 1},
        reason="why this tool",
    )
    """

    def __init__(self) -> None:
        self._logs: list[dict] = []

    # ── Core logging ──────────────────────────────────────────────────────────

    def log(
        self,
        task_id:     str,
        tool_name:   str,
        input_data:  dict,
        output_data: dict | None,
        success:     bool,
        error:       str | None = None,
        reason:      str | None = None,
    ) -> dict:
        """
        Record a single tool call.

        Returns the log entry dict (same object stored internally).
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "task_id":   task_id,
            "tool_name": tool_name,
            "input":     input_data,
            "output":    output_data,
            "success":   success,
            "error":     error,
            "reason":    reason,
        }
        self._logs.append(entry)
        return entry

    def call(
        self,
        task_id:    str,
        tool_name:  str,
        tool_fn,
        input_data: dict,
        reason:     str | None = None,
    ) -> tuple[dict | None, dict]:
        """
        Call tool_fn(**input_data), log the result, return (output, log_entry).

        Any exception is caught and logged as a failure; output will be None.
        """
        try:
            output = tool_fn(**input_data)
            entry  = self.log(task_id, tool_name, input_data, output,
                              True, None, reason)
            return output, entry
        except Exception as exc:
            entry = self.log(task_id, tool_name, input_data, None,
                             False, str(exc), reason)
            return None, entry

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_logs(self) -> list[dict]:
        return list(self._logs)

    def get_task_logs(self, task_id: str) -> list[dict]:
        return [e for e in self._logs if e["task_id"] == task_id]

    def clear(self) -> None:
        self._logs.clear()

    # ── Aggregate metrics ─────────────────────────────────────────────────────

    def summary(self) -> dict:
        """
        Compute aggregate metrics.

        Returns
        -------
        dict
          total_calls, successful, failed, success_rate,
          tool_counts, task_ids, avg_calls_per_task
        """
        total      = len(self._logs)
        successful = sum(1 for e in self._logs if e["success"])
        failed     = total - successful

        tool_counts: dict[str, int] = {}
        for e in self._logs:
            tool_counts[e["tool_name"]] = tool_counts.get(e["tool_name"], 0) + 1

        task_ids = sorted(set(e["task_id"] for e in self._logs))
        avg      = round(total / len(task_ids), 2) if task_ids else 0.0

        return {
            "total_calls":        total,
            "successful":         successful,
            "failed":             failed,
            "success_rate":       round(successful / total, 4) if total else 1.0,
            "tool_counts":        tool_counts,
            "task_ids":           task_ids,
            "avg_calls_per_task": avg,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_jsonl(self, path: str | Path) -> int:
        """Save all logs to a JSON Lines file. Returns number of lines written."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(e, ensure_ascii=False) for e in self._logs]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return len(lines)

    def __len__(self) -> int:
        return len(self._logs)

    def __repr__(self) -> str:
        s = self.summary()
        return (
            f"ToolCallLogger("
            f"calls={s['total_calls']}, "
            f"success_rate={s['success_rate']:.1%})"
        )
