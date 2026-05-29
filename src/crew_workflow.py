"""
crew_workflow.py — CrewWorkflow orchestrates the multi-agent pipeline.

Pipeline
--------
Triager → Extractor → Reviewer → RepairAgent? → FallbackHandler? → Final Output

Delegation rules
----------------
1. Triager is always called first.
2. Extractor is always called after Triager.
3. Reviewer always checks Extractor output.
4. verdict=accept              → final output, status="accepted"
5. verdict=repair_needed       → RepairAgent → re-review
      re-review accept         → status="accepted_after_repair"
      re-review not accept     → status="manual_review"
6. verdict=fallback_needed     → FallbackHandler → status="fallback"
7. verdict=manual_review       → status="manual_review" (no further agents)
"""
from __future__ import annotations
from dataclasses import dataclass, field

try:
    from agents import TriagerAgent, ExtractorAgent
    from reviewer import ReviewerAgent
    from fallback import RepairAgent, FallbackHandler
except ImportError:
    from src.agents import TriagerAgent, ExtractorAgent
    from src.reviewer import ReviewerAgent
    from src.fallback import RepairAgent, FallbackHandler


# ── Crew Result ───────────────────────────────────────────────────────────────

@dataclass
class CrewResult:
    case_id:           str
    input:             str
    triager_output:    dict
    extractor_output:  dict
    reviewer_output:   dict
    fallback_triggered: bool
    fallback_output:   dict | None
    final_output:      dict
    status:            str
    agents_called:     list

    def to_log_dict(self) -> dict:
        return {
            "case_id":            self.case_id,
            "input":              self.input,
            "triager_output":     self.triager_output,
            "extractor_output":   self.extractor_output,
            "reviewer_output":    self.reviewer_output,
            "fallback_triggered": self.fallback_triggered,
            "fallback_output":    self.fallback_output,
            "final_output":       self.final_output,
            "status":             self.status,
            "agents_called":      self.agents_called,
        }

    def summary_line(self) -> str:
        n    = len(self.agents_called)
        cat  = self.final_output.get("category", "?")
        fb   = " [FALLBACK]" if self.fallback_triggered else ""
        return (
            f"[{self.case_id}] {self.status:<28} | "
            f"agents={n} | cat={str(cat):<28}{fb}"
        )


# ── Crew Workflow ─────────────────────────────────────────────────────────────

class CrewWorkflow:
    """
    Orchestrates the four-agent crew.

    Parameters
    ----------
    None — all agents are stateless and instantiated internally.
    """

    def __init__(self) -> None:
        self._triager   = TriagerAgent()
        self._extractor = ExtractorAgent()
        self._reviewer  = ReviewerAgent()
        self._repair    = RepairAgent()
        self._fallback  = FallbackHandler()

    def run(
        self,
        text: str,
        case_id: str,
        pre_extracted: dict | None = None,
    ) -> CrewResult:
        agents_called: list[str] = []

        # ── 1. Triage ──────────────────────────────────────────────────────────
        triage = self._triager.triage(text, case_id)
        agents_called.append("Triager")

        # ── 2. Extract ─────────────────────────────────────────────────────────
        extraction = self._extractor.extract(text, triage, case_id, pre_extracted)
        agents_called.append("Extractor")

        # ── 3. Review ──────────────────────────────────────────────────────────
        review = self._reviewer.review(text, triage, extraction, case_id)
        agents_called.append("Reviewer")

        # ── 4. Verdict handling ────────────────────────────────────────────────
        fallback_triggered = False
        fallback_output    = None
        final_output       = extraction
        status             = "accepted"

        if review.verdict == "accept":
            status = "accepted"

        elif review.verdict == "repair_needed":
            fallback_triggered = True
            repaired           = self._repair.repair(text, extraction, review, case_id)
            agents_called.append("RepairAgent")

            re_review = self._reviewer.review(text, triage, repaired, case_id)
            agents_called.append("Reviewer (re-check)")

            fallback_output = repaired
            if re_review.verdict == "accept":
                final_output = repaired
                status       = "accepted_after_repair"
            else:
                final_output = repaired
                status       = "manual_review"

        elif review.verdict == "fallback_needed":
            fallback_triggered = True
            fb_result          = self._fallback.handle(text, extraction, review, case_id)
            agents_called.append("FallbackHandler")
            fallback_output = fb_result
            final_output    = fb_result
            status          = "fallback"

        else:  # manual_review (directly from Reviewer)
            status = "manual_review"

        return CrewResult(
            case_id=case_id,
            input=text,
            triager_output=triage.to_dict(),
            extractor_output=extraction,
            reviewer_output=review.to_dict(),
            fallback_triggered=fallback_triggered,
            fallback_output=fallback_output,
            final_output=final_output,
            status=status,
            agents_called=agents_called,
        )
