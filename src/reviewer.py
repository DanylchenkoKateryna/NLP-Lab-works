"""
reviewer.py — ReviewerAgent for Lab 13 multi-agent crew.

Checks extraction output for:
  1. Schema validity (required fields + types)
  2. Category consistency (keyword evidence vs extracted category)
  3. Hallucination (entities not present in source text)
  4. Completeness (long text but empty entities)
  5. Relative dates (flags for manual normalization)
"""
from __future__ import annotations
from dataclasses import dataclass, field

try:
    from agents import _ELECTRONICS_KW, _CHRISTIAN_KW, _ATHEISM_KW
except ImportError:
    from src.agents import _ELECTRONICS_KW, _CHRISTIAN_KW, _ATHEISM_KW

_REQUIRED_FIELDS: tuple[str, ...] = (
    "category", "persons", "organizations", "locations", "dates"
)

_VALID_CATEGORIES: frozenset[str] = frozenset({
    "sci.electronics", "soc.religion.christian", "alt.atheism",
    "unknown", "ambiguous",
})

_RELATIVE_DATE_KW: tuple[str, ...] = (
    "next month", "last month", "yesterday", "tomorrow",
    "next week", "last week", "this year", "last year", "next year",
    "recently", "soon", "upcoming", "next spring", "next summer",
    "last spring", "last summer",
)

_CAT_FROM_DOMAIN: dict[str, str] = {
    "electronics": "sci.electronics",
    "christian":   "soc.religion.christian",
    "atheism":     "alt.atheism",
}


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class ReviewResult:
    verdict: str            # accept | repair_needed | fallback_needed | manual_review
    valid_json: bool
    schema_ok: bool
    consistency_ok: bool
    issues: list
    recommended_action: str

    def to_dict(self) -> dict:
        return {
            "verdict":            self.verdict,
            "valid_json":         self.valid_json,
            "schema_ok":          self.schema_ok,
            "consistency_ok":     self.consistency_ok,
            "issues":             self.issues,
            "recommended_action": self.recommended_action,
        }


# ── Reviewer ──────────────────────────────────────────────────────────────────

class ReviewerAgent:
    """
    Reviews extractor output and issues a structured verdict.

    Verdict rules
    -------------
    hallucination found       → fallback_needed
    schema error              → repair_needed
    ambiguous + already tried → manual_review
    ambiguous (first time)    → repair_needed  (attempt resolution)
    category inconsistency    → repair_needed
    soft issues + repaired    → accept  (issue already acknowledged)
    soft issues only          → repair_needed
    no issues                 → accept
    """

    def review(
        self,
        text: str,
        triage,         # TriageResult
        extraction: dict,
        task_id: str,
    ) -> ReviewResult:
        issues: list[dict] = []

        # ── guard: must be a dict ──────────────────────────────────────────────
        if not isinstance(extraction, dict):
            return ReviewResult(
                verdict="fallback_needed",
                valid_json=False,
                schema_ok=False,
                consistency_ok=False,
                issues=[{"field": "_all", "problem": "extraction is not a dict"}],
                recommended_action="run_fallback_extraction",
            )

        # ── extraction_failed flag ─────────────────────────────────────────────
        if extraction.get("_extraction_failed"):
            return ReviewResult(
                verdict="fallback_needed",
                valid_json=True,
                schema_ok=False,
                consistency_ok=False,
                issues=[{"field": "_all", "problem": "extraction failed — empty input"}],
                recommended_action="manual_review_empty_input",
            )

        valid_json = True

        # ── 1. Schema check ────────────────────────────────────────────────────
        schema_ok = True
        for f in _REQUIRED_FIELDS:
            if f not in extraction:
                issues.append({"field": f, "problem": f"missing required field '{f}'"})
                schema_ok = False

        for arr in ("persons", "organizations", "locations", "dates"):
            if arr in extraction and not isinstance(extraction[arr], list):
                issues.append({
                    "field": arr,
                    "problem": f"field '{arr}' must be list, got {type(extraction[arr]).__name__}",
                })
                schema_ok = False

        # ── 2. Category consistency ────────────────────────────────────────────
        consistency_ok = True
        extracted_cat  = extraction.get("category")

        if extracted_cat is None:
            issues.append({"field": "category", "problem": "category is null"})
            consistency_ok = False

        elif extracted_cat == "ambiguous":
            issues.append({
                "field":   "category",
                "problem": "ambiguous category — cannot route to specific class",
            })
            consistency_ok = False

        elif text and text.strip() and extracted_cat not in ("unknown",):
            lo = text.lower()
            kw_scores = {
                "sci.electronics":        sum(1 for kw in _ELECTRONICS_KW if kw in lo),
                "soc.religion.christian": sum(1 for kw in _CHRISTIAN_KW   if kw in lo),
                "alt.atheism":            sum(1 for kw in _ATHEISM_KW      if kw in lo),
            }
            total_kw = sum(kw_scores.values())
            if total_kw > 0:
                kw_vals = sorted(kw_scores.values(), reverse=True)
                is_tie  = kw_vals[0] == kw_vals[1] and kw_vals[1] > 0
                top_cat = max(kw_scores, key=kw_scores.get)
                if is_tie and extracted_cat != "ambiguous":
                    issues.append({
                        "field":   "category",
                        "problem": "keyword evidence is tied but category is not 'ambiguous'",
                    })
                    consistency_ok = False
                elif not is_tie and top_cat != extracted_cat:
                    issues.append({
                        "field":   "category",
                        "problem": (
                            f"keyword evidence suggests '{top_cat}' "
                            f"but extracted '{extracted_cat}'"
                        ),
                    })
                    consistency_ok = False

        # ── 3. Hallucination detection ─────────────────────────────────────────
        hallucination_found = False
        if text:
            lo = text.lower()
            for arr in ("persons", "organizations", "locations"):
                for entity in extraction.get(arr, []):
                    if entity and entity.lower() not in lo:
                        issues.append({
                            "field":   arr,
                            "problem": f"hallucinated entity '{entity}' not found in text",
                            "entity":  entity,
                        })
                        hallucination_found = True

        # ── 4. Completeness check ──────────────────────────────────────────────
        if text and len(text.split()) > 15:
            all_empty = all(
                not extraction.get(f, [])
                for f in ("persons", "organizations", "locations", "dates")
            )
            if all_empty and extracted_cat not in (None, "unknown", "ambiguous"):
                issues.append({
                    "field":   "_entities",
                    "problem": "long text but all entity lists empty — possible incomplete extraction",
                })

        # ── 5. Relative date check ─────────────────────────────────────────────
        if text:
            lo = text.lower()
            for rel in _RELATIVE_DATE_KW:
                if rel in lo:
                    issues.append({
                        "field":   "dates",
                        "problem": f"relative date '{rel}' found — normalization needed",
                    })
                    break

        # ── Verdict ────────────────────────────────────────────────────────────
        already_repaired = extraction.get("_repaired", False)
        needs_manual     = extraction.get("needs_manual_review", False)

        if hallucination_found:
            verdict = "fallback_needed"
            action  = "remove_hallucinated_entities_via_fallback"

        elif not schema_ok:
            verdict = "repair_needed"
            action  = "fill_missing_fields"

        elif extracted_cat == "ambiguous":
            if already_repaired and needs_manual:
                verdict = "manual_review"
                action  = "manual_review_ambiguous_category"
            else:
                verdict = "repair_needed"
                action  = "attempt_category_resolution"

        elif not consistency_ok:
            verdict = "repair_needed"
            action  = "fix_category_inconsistency"

        elif issues and already_repaired and needs_manual:
            # Soft issues already acknowledged by prior repair → accept
            verdict = "accept"
            action  = "accepted_with_acknowledged_flags"

        elif issues:
            verdict = "repair_needed"
            action  = "repair_minor_issues"

        else:
            verdict = "accept"
            action  = "none"

        return ReviewResult(
            verdict=verdict,
            valid_json=valid_json,
            schema_ok=schema_ok,
            consistency_ok=consistency_ok,
            issues=issues,
            recommended_action=action,
        )
