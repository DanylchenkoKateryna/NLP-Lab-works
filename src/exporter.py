"""
exporter.py — Export step for Lab 14 NLP flow.

Converts the final FlowState into three structured output formats:
  1. JSON   — structured dict suitable for downstream systems
  2. Markdown — human-readable report
  3. CSV row  — single row for batch analysis

Export is stable even when the flow failed:
  - Always returns a structured dict, never raises.
  - Uses state.status and state.errors to signal failure clearly.
"""
from __future__ import annotations

try:
    from flow_state import FlowState
except ImportError:
    from src.flow_state import FlowState


_CSV_HEADER = (
    "case_id,route,category,confidence,"
    "persons,organizations,locations,dates,"
    "status,fallback_triggered,warnings_count,errors_count"
)


def export_step(state: FlowState) -> FlowState:
    """
    Build structured exports from state.final_output.

    Updates state.export_output with keys:
      json, markdown, csv_row, csv_header.
    """
    out = state.final_output or {}

    # ── JSON export ───────────────────────────────────────────────────────────
    json_export: dict = {
        "case_id":            state.case_id,
        "route":              state.route,
        "schema_name":        state.schema_name,
        "routing_reason":     state.routing_reason,
        "final_output":       out,
        "status":             state.status,
        "fallback_triggered": state.fallback_triggered,
        "fallback_strategy":  state.fallback_strategy,
        "warnings":           state.warnings,
        "errors":             state.errors,
    }

    # ── Markdown report ───────────────────────────────────────────────────────
    category   = out.get("category") or "N/A"
    confidence = out.get("confidence")
    conf_str   = f"{confidence:.3f}" if isinstance(confidence, float) else str(confidence or "N/A")

    md_lines = [
        f"# Flow Export — {state.case_id}",
        "",
        f"**Route:** `{state.route}`  ",
        f"**Schema:** `{state.schema_name}`  ",
        f"**Status:** `{state.status}`  ",
        f"**Category:** `{category}`  ",
        f"**Confidence:** `{conf_str}`  ",
        f"**Fallback triggered:** `{state.fallback_triggered}`",
        "",
        "## Entities",
        "",
        f"- Persons: {out.get('persons', [])}",
        f"- Organizations: {out.get('organizations', [])}",
        f"- Locations: {out.get('locations', [])}",
        f"- Dates: {out.get('dates', [])}",
        "",
        "## Routing",
        "",
        f"- Reason: {state.routing_reason}",
        f"- Keyword scores: {state.keyword_scores}",
        "",
    ]
    if state.warnings:
        md_lines += ["## Warnings", ""] + [f"- {w}" for w in state.warnings] + [""]
    if state.errors:
        md_lines += ["## Errors", ""] + [f"- {e}" for e in state.errors] + [""]
    md_report = "\n".join(md_lines)

    # ── CSV row ───────────────────────────────────────────────────────────────
    def _join(lst) -> str:
        return "|".join(str(x) for x in lst) if isinstance(lst, list) else ""

    csv_row = ",".join([
        state.case_id,
        state.route,
        str(category),
        conf_str,
        _join(out.get("persons", [])),
        _join(out.get("organizations", [])),
        _join(out.get("locations", [])),
        _join(out.get("dates", [])),
        state.status,
        str(state.fallback_triggered),
        str(len(state.warnings)),
        str(len(state.errors)),
    ])

    state.export_output = {
        "json":       json_export,
        "markdown":   md_report,
        "csv_row":    csv_row,
        "csv_header": _CSV_HEADER,
    }
    state.log_step(
        "export",
        "ok",
        formats=["json", "markdown", "csv"],
        final_status=state.status,
    )
    return state
