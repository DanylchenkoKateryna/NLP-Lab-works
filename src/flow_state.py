"""
flow_state.py — FlowState dataclass for Lab 14 stateful NLP flow.

The state object is the single source of truth for a case as it moves
through: ingest → route → execute → validate → export.

Memory / knowledge policy (summary)
------------------------------------
- State stores only case-level data for the current run.
- Knowledge (keyword lists, schemas, route definitions) is read-only
  and lives outside state.
- Invalid intermediate outputs are logged as errors, never accepted as truth.
- No API keys or credentials are stored here.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FlowState:
    # ── Identity ───────────────────────────────────────────────────────────────
    case_id:    str = ""
    raw_text:   str = ""
    clean_text: str = ""

    # ── Status ─────────────────────────────────────────────────────────────────
    # Values: initialized | ingested | routed | executed | validated
    #         | exported | exported_with_warning | accepted_after_repair
    #         | accepted_after_repair_with_warning | manual_review | failed
    status:   str        = "initialized"
    errors:   list[str]  = field(default_factory=list)
    warnings: list[str]  = field(default_factory=list)

    # ── Route (set by route step) ───────────────────────────────────────────────
    route:           str        = ""   # e.g. "electronics_deep"
    schema_name:     str        = ""   # e.g. "electronics_schema"
    required_fields: list[str]  = field(default_factory=list)
    routing_reason:  str        = ""
    keyword_scores:  dict       = field(default_factory=dict)

    # ── Execute (set by execute step) ──────────────────────────────────────────
    execute_output: dict = field(default_factory=dict)
    execute_method: str  = ""
    execute_error:  str  = ""

    # ── Validate (set by validate step) ────────────────────────────────────────
    validation_result: dict = field(default_factory=dict)

    # ── Fallback (set by fallback step) ────────────────────────────────────────
    fallback_triggered: bool       = False
    fallback_result:    dict | None = None
    fallback_strategy:  str        = ""

    # ── Export (set by export step) ────────────────────────────────────────────
    final_output:  dict = field(default_factory=dict)
    export_output: dict = field(default_factory=dict)

    # ── Steps log (append-only audit trail) ───────────────────────────────────
    steps: list[dict] = field(default_factory=list)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def log_step(self, step: str, status: str, **kwargs) -> None:
        """Append one step entry to the audit trail."""
        entry = {"step": step, "status": status}
        entry.update(kwargs)
        self.steps.append(entry)

    def add_error(self, msg: str) -> None:
        if msg not in self.errors:
            self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)

    def to_dict(self) -> dict:
        """Return full state as a plain dict (for logging / serialisation)."""
        return {
            "case_id":            self.case_id,
            "raw_text":           self.raw_text,
            "clean_text":         self.clean_text,
            "status":             self.status,
            "route":              self.route,
            "schema_name":        self.schema_name,
            "routing_reason":     self.routing_reason,
            "keyword_scores":     self.keyword_scores,
            "execute_output":     self.execute_output,
            "execute_method":     self.execute_method,
            "validation_result":  self.validation_result,
            "fallback_triggered": self.fallback_triggered,
            "fallback_result":    self.fallback_result,
            "fallback_strategy":  self.fallback_strategy,
            "final_output":       self.final_output,
            "export_output":      self.export_output,
            "errors":             self.errors,
            "warnings":           self.warnings,
            "steps":              self.steps,
        }
