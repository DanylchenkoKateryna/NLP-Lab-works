"""
fallback.py — RepairAgent and FallbackHandler for Lab 13 multi-agent crew.

RepairAgent   : fixes specific issues found by ReviewerAgent.
FallbackHandler: handles cases where repair is insufficient.
"""
from __future__ import annotations
import re

try:
    from tools import extract_entities, classify_category
    from agents import _ELECTRONICS_KW, _CHRISTIAN_KW, _ATHEISM_KW, REQUIRED_FIELDS
except ImportError:
    from src.tools import extract_entities, classify_category
    from src.agents import _ELECTRONICS_KW, _CHRISTIAN_KW, _ATHEISM_KW, REQUIRED_FIELDS

_DOMAIN_TO_CAT: dict[str, str] = {
    "electronics": "sci.electronics",
    "christian":   "soc.religion.christian",
    "atheism":     "alt.atheism",
}


# ── Repair Agent ──────────────────────────────────────────────────────────────

class RepairAgent:
    """
    Applies targeted fixes to an extraction based on reviewer issues.

    Repairs performed
    -----------------
    - Fill missing required fields (None / [])
    - Remove hallucinated entities (not found in source text)
    - Fix wrong category if keyword evidence is clear
    - Attempt to resolve ambiguous category via keyword counts
    - Mark relative dates with needs_manual_review flag
    """

    def repair(
        self,
        text: str,
        extraction: dict,
        review,         # ReviewResult
        task_id: str,
    ) -> dict:
        repaired = dict(extraction)

        # ── Fill missing required fields ───────────────────────────────────────
        for f in REQUIRED_FIELDS:
            if f not in repaired:
                repaired[f] = None if f == "category" else []

        # ── Remove hallucinated entities ───────────────────────────────────────
        hallucinated_entities = {
            issue["entity"]
            for issue in review.issues
            if issue.get("entity") and "hallucinated" in issue.get("problem", "")
        }
        if hallucinated_entities and text:
            lo = text.lower()
            for arr in ("persons", "organizations", "locations"):
                repaired[arr] = [
                    e for e in repaired.get(arr, [])
                    if e.lower() in lo
                ]

        # ── Fix category issues ────────────────────────────────────────────────
        cat_issues = [i for i in review.issues if i.get("field") == "category"]
        for issue in cat_issues:
            prob = issue.get("problem", "")

            if "keyword evidence suggests" in prob:
                m = re.search(r"suggests '([^']+)'", prob)
                if m:
                    repaired["category"] = m.group(1)
                    break

            if "ambiguous" in prob or repaired.get("category") == "ambiguous":
                if text and text.strip():
                    lo = text.lower()
                    domain_scores = {
                        "electronics": sum(1 for kw in _ELECTRONICS_KW if kw in lo),
                        "christian":   sum(1 for kw in _CHRISTIAN_KW   if kw in lo),
                        "atheism":     sum(1 for kw in _ATHEISM_KW      if kw in lo),
                    }
                    total = sum(domain_scores.values())
                    if total > 0:
                        vals = sorted(domain_scores.values(), reverse=True)
                        still_tied = vals[0] == vals[1] and vals[1] > 0
                        if not still_tied:
                            top = max(domain_scores, key=domain_scores.get)
                            repaired["category"] = _DOMAIN_TO_CAT[top]
                        else:
                            repaired["needs_manual_review"] = True
                            repaired["_repair_note"] = (
                                "ambiguous category cannot be resolved — "
                                "keyword counts still tied"
                            )
                break

        # ── Mark relative dates ────────────────────────────────────────────────
        date_issues = [
            i for i in review.issues
            if i.get("field") == "dates" and "relative" in i.get("problem", "")
        ]
        if date_issues:
            repaired["has_relative_date"] = True
            repaired["needs_manual_review"] = True
            if "_repair_note" not in repaired:
                repaired["_repair_note"] = (
                    "relative date detected — manual normalization needed"
                )

        repaired["_repaired"] = True
        return repaired


# ── Fallback Handler ──────────────────────────────────────────────────────────

class FallbackHandler:
    """
    Handles extraction failures that repair cannot fix.

    Strategy 1: Rule-based re-extraction from scratch.
    Strategy 2: Safe failure — return partial output with error flag.
    """

    def handle(
        self,
        text: str,
        extraction: dict,
        review,         # ReviewResult
        task_id: str,
    ) -> dict:
        # ── Strategy 1: Re-extract from scratch ───────────────────────────────
        if text and text.strip():
            try:
                entities = extract_entities(text)
                clf      = classify_category(text)
                return {
                    "category":        clf["category"],
                    "persons":         entities["persons"],
                    "organizations":   entities["organizations"],
                    "locations":       entities["locations"],
                    "dates":           entities["dates"],
                    "confidence_note": "fallback rule-based re-extraction",
                    "needs_manual_review": (
                        clf["is_ambiguous"] or entities["raw_count"] == 0
                    ),
                    "_fallback":        True,
                    "_fallback_reason": review.recommended_action,
                    "_fallback_strategy": "rule_based_reextraction",
                }
            except (ValueError, TypeError):
                pass

        # ── Strategy 2: Safe failure ───────────────────────────────────────────
        partial: dict = {}
        for f in ("category", "persons", "organizations", "locations", "dates"):
            val = extraction.get(f)
            if val is not None and val != [] and val != "ambiguous":
                partial[f] = val

        reason = (
            review.issues[0]["problem"]
            if review.issues
            else "unknown failure"
        )
        return {
            "status":              "failed",
            "reason":              reason,
            "partial_output":      partial,
            "needs_manual_review": True,
            "_fallback":           True,
            "_fallback_strategy":  "safe_failure",
        }
