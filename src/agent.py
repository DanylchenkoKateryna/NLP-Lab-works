"""
agent.py — Single tool-grounded agent for 20 Newsgroups post analysis.

Agent cycle
-----------
1. Receive task (text + task_id)
2. Call extract_entities  → structured entity dict
3. Call classify_category → category + confidence
4. Adaptive: call validate_extraction if text is non-trivial
5. Synthesize final AgentResult from tool outputs
6. All calls logged via ToolCallLogger

No LLM API required — rule-based planning, fully deterministic.
Replace the planning logic with an LLM tool-selector in production.
"""

from __future__ import annotations
from dataclasses import dataclass, field

try:
    from tool_logger import ToolCallLogger
    from tools import extract_entities, classify_category, validate_extraction
except ImportError:
    from src.tool_logger import ToolCallLogger
    from src.tools import extract_entities, classify_category, validate_extraction


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Full trace of a single agent run."""
    task_id:       str
    text:          str
    tools_called:  list[str]  = field(default_factory=list)
    tool_outputs:  dict       = field(default_factory=dict)
    final_answer:  dict       = field(default_factory=dict)
    success:       bool       = True
    error_message: str | None = None
    n_tool_calls:  int        = 0

    def summary_line(self) -> str:
        status = "OK  " if self.success else "FAIL"
        cat    = self.final_answer.get("category", "?")
        n      = self.final_answer.get("entity_count", 0)
        return (
            f"[{self.task_id}] {status} | "
            f"tools={self.n_tool_calls} | "
            f"category={cat:<28} | entities={n}"
        )


# ── Agent ─────────────────────────────────────────────────────────────────────

class SingleAgent:
    """
    Tool-grounded agent for structured extraction from newsgroup posts.

    Tool-selection policy
    ---------------------
    Always called  : extract_entities, classify_category
    Called if needed: validate_extraction
      Triggered when extraction found ≥ 1 entity  OR  text length > 60 chars.
      Skipped for very short texts with zero entities (validation adds nothing).

    Parameters
    ----------
    logger : ToolCallLogger  Shared logger — all calls recorded here.
    """

    def __init__(self, logger: ToolCallLogger) -> None:
        self.logger = logger

    # ── Execution ─────────────────────────────────────────────────────────────

    def run(self, text: str, task_id: str) -> AgentResult:
        """
        Execute the full agent cycle for one input.

        Parameters
        ----------
        text    : Raw text to analyse.
        task_id : Unique identifier used in all log entries.

        Returns
        -------
        AgentResult  with tool outputs, final answer, call count.
        """
        result = AgentResult(task_id=task_id, text=text)
        tool_outputs: dict = {}

        # ── Step 1: Extract entities ──────────────────────────────────────────
        extraction, _ = self.logger.call(
            task_id=task_id,
            tool_name="extract_entities",
            tool_fn=extract_entities,
            input_data={"text": text},
            reason="Extract persons, orgs, locations, dates from raw text",
        )
        result.tools_called.append("extract_entities")
        result.n_tool_calls += 1

        if extraction is None:
            result.success       = False
            result.error_message = "extract_entities failed — aborting pipeline"
            result.final_answer  = {
                "task_id": task_id, "status": "error",
                "error":   "Entity extraction failed — cannot continue",
            }
            return result

        tool_outputs["extraction"] = extraction

        # ── Step 2: Classify category ─────────────────────────────────────────
        classification, _ = self.logger.call(
            task_id=task_id,
            tool_name="classify_category",
            tool_fn=classify_category,
            input_data={"text": text},
            reason="Classify text into newsgroup category with confidence score",
        )
        result.tools_called.append("classify_category")
        result.n_tool_calls += 1

        if classification is None:
            result.success       = False
            result.error_message = "classify_category failed"
            result.final_answer  = {
                "task_id": task_id, "status": "error",
                "error":   "Classification failed",
                "entities": extraction,
            }
            return result

        tool_outputs["classification"] = classification

        # ── Step 3 (adaptive): Validate ───────────────────────────────────────
        has_entities = extraction.get("raw_count", 0) > 0
        long_text    = len((text or "")) > 60
        validation   = None

        if has_entities or long_text:
            composed = {
                "category":      classification["category"],
                "persons":       extraction["persons"],
                "organizations": extraction["organizations"],
                "locations":     extraction["locations"],
                "dates":         extraction["dates"],
            }
            validation, _ = self.logger.call(
                task_id=task_id,
                tool_name="validate_extraction",
                tool_fn=validate_extraction,
                input_data={"data": composed},
                reason="Validate schema and consistency of composed extraction",
            )
            result.tools_called.append("validate_extraction")
            result.n_tool_calls += 1

        tool_outputs["validation"] = validation

        # ── Step 4: Synthesise final answer ───────────────────────────────────
        result.tool_outputs = tool_outputs
        result.final_answer = _synthesise(task_id, extraction, classification, validation)
        return result


# ── Synthesis (pure function) ─────────────────────────────────────────────────

def _synthesise(
    task_id:        str,
    extraction:     dict,
    classification: dict,
    validation:     dict | None,
) -> dict:
    """Build final structured answer from tool outputs."""
    val_status   = "skipped"
    val_errors:   list[str] = []
    val_warnings: list[str] = []

    if validation is not None:
        val_status   = "valid" if validation["valid"] else "invalid"
        val_errors   = validation.get("errors",   [])
        val_warnings = validation.get("warnings", [])

    return {
        "task_id":       task_id,
        "status":        "ok" if not val_errors else "validation_failed",
        "category":      classification["category"],
        "confidence":    classification["confidence"],
        "is_ambiguous":  classification["is_ambiguous"],
        "persons":       extraction["persons"],
        "organizations": extraction["organizations"],
        "locations":     extraction["locations"],
        "dates":         extraction["dates"],
        "entity_count":  extraction["raw_count"],
        "validation":    val_status,
        "val_errors":    val_errors,
        "val_warnings":  val_warnings,
    }
