"""
flow_logger.py — JSONL logging for Lab 14 NLP flow.

One JSON line per case is appended to flow_logs_lab14.jsonl.
The log captures all required fields from the lab spec:
  case_id, input, steps, route, validation_result,
  fallback_triggered, fallback_result, export_output,
  final_status, errors, warnings.

Policy
------
- Logs are append-only; no case record is ever overwritten.
- No API keys, credentials, or private data are written.
- Invalid intermediate outputs are logged as errors, not as truth.
"""
from __future__ import annotations
import json
from pathlib import Path

try:
    from flow_state import FlowState
except ImportError:
    from src.flow_state import FlowState


def log_flow_result(state: FlowState, log_path: str | Path) -> None:
    """
    Append a single JSONL record for *state* to *log_path*.

    Creates the parent directory if it doesn't exist.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "case_id":            state.case_id,
        "input":              state.raw_text,
        "route":              state.route,
        "steps":              state.steps,
        "execute_method":     state.execute_method,
        "validation_result":  state.validation_result,
        "fallback_triggered": state.fallback_triggered,
        "fallback_strategy":  state.fallback_strategy,
        "fallback_result":    state.fallback_result,
        "export_output":      state.export_output.get("json", {}),
        "final_status":       state.status,
        "errors":             state.errors,
        "warnings":           state.warnings,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_flow_logs(log_path: str | Path) -> list[dict]:
    """Read all JSONL records from *log_path*. Returns [] if file missing."""
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    records: list[dict] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
