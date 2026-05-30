"""
flow.py — NLPFlow: stateful 5-stage orchestrator for Lab 14.

Pipeline
--------
ingest → route → execute → validate → export

Delegation rules
----------------
1. ingest always runs first: creates case_id, stores raw + clean text.
2. route always runs after ingest: determines route, schema, required fields.
3. execute always runs after route: calls NLP tools per route.
4. validate always runs after execute: checks schema, hallucinations,
   category consistency, confidence, relative dates.
5. Based on validate verdict:
   - accept              → export (status=exported)
   - export_with_warning → export (status=exported_with_warning)
   - repair              → RepairFallback → re-validate → export or manual_review
   - fallback            → RuleBasedFallback → re-validate → export or manual_review
   - manual_review       → export (status=manual_review, no further agents)
   - safe_failure        → export (status=failed)
6. export always runs last: produces JSON + Markdown + CSV.

Memory / knowledge policy
--------------------------
- State stores only case-level data for the current run.
- Knowledge (keyword lists, schemas) is read-only — lives in tools.py / router.py.
- Invalid intermediate outputs are logged as errors, never accepted as truth.
- No API keys, credentials, or private data are stored in state.
"""
from __future__ import annotations
import re

try:
    from flow_state import FlowState
    from router import route_step, ROUTE_EMPTY, ROUTE_AMBIGUOUS, ROUTE_UNKNOWN
    from executor import execute_step
    from exporter import export_step
    from tools import classify_category, extract_entities, validate_extraction
except ImportError:
    from src.flow_state import FlowState
    from src.router import route_step, ROUTE_EMPTY, ROUTE_AMBIGUOUS, ROUTE_UNKNOWN
    from src.executor import execute_step
    from src.exporter import export_step
    from src.tools import classify_category, extract_entities, validate_extraction


# ── Relative-date detector ────────────────────────────────────────────────────

_REL_DATE_UNIGRAMS = frozenset([
    "yesterday", "tomorrow", "tonight", "today",
    "recently", "soon", "upcoming", "forthcoming",
])
_REL_DATE_BIGRAMS = frozenset([
    "next week", "last week", "this week",
    "next month", "last month", "this month",
    "next year", "last year", "this year",
])


def _has_relative_date(text: str) -> bool:
    lo     = text.lower()
    tokens = re.split(r"\s+", lo)
    for w in _REL_DATE_UNIGRAMS:
        if w in tokens:
            return True
    bigrams = {tokens[i] + " " + tokens[i + 1] for i in range(len(tokens) - 1)}
    return bool(bigrams & _REL_DATE_BIGRAMS)


def _is_hallucination(entity: str, text: str) -> bool:
    return entity.lower() not in text.lower()


# ── Validate step ─────────────────────────────────────────────────────────────

def _validate_step(state: FlowState) -> FlowState:
    """
    Validate the execute output.  Sets state.validation_result with:
      valid, schema_ok, required_fields_ok, issues[], recommended_action.

    Checks performed
    ----------------
    1. Empty / failed extraction  → safe_failure immediately
    2. Schema validity (tools.validate_extraction)
    3. Hallucination detection    → fallback (re-extract from scratch)
    4. Category consistency       → repair
    5. Relative-date detection    → export_with_warning
    6. Confidence threshold < 0.3 → export_with_warning
    7. Ambiguous category         → manual_review
    """
    out    = state.execute_output
    text   = state.clean_text
    issues: list[dict] = []

    # 1. Extraction failed / empty input
    if out.get("_extraction_failed"):
        state.validation_result = {
            "valid":              False,
            "schema_ok":          False,
            "required_fields_ok": False,
            "issues":             [{"field": "input", "problem": out.get("_reason", "extraction failed")}],
            "recommended_action": "safe_failure",
        }
        state.status = "validated"
        state.log_step("validate", "failed", action="safe_failure")
        return state

    # 2. Schema check (reuse tools.validate_extraction — stdlib only)
    schema_res = validate_extraction(out)
    for err in schema_res["errors"]:
        issues.append({"field": "schema", "problem": err})
    # Schema warnings are non-blocking — surface as soft issues → export_with_warning
    for warn in schema_res.get("warnings", []):
        issues.append({"field": "schema_warning", "problem": warn})

    # 3. Hallucination check
    for fld in ("persons", "organizations", "locations"):
        for entity in out.get(fld, []):
            if _is_hallucination(entity, text):
                issues.append({
                    "field":   fld,
                    "problem": f"hallucination: '{entity}' not found in source text",
                })

    # 4. Category consistency
    category = out.get("category", "unknown")
    if text and category not in ("unknown", "ambiguous", None):
        try:
            cls = classify_category(text)
            if not cls["is_ambiguous"] and cls["category"] != "unknown":
                if cls["category"] != category:
                    issues.append({
                        "field":   "category",
                        "problem": (
                            f"category '{category}' inconsistent with "
                            f"keyword evidence → expected '{cls['category']}'"
                        ),
                    })
        except Exception:
            pass

    # 5. Relative dates
    if _has_relative_date(text):
        issues.append({
            "field":   "dates",
            "problem": "relative date expression detected — cannot normalize without reference date",
        })

    # 6. Confidence threshold
    conf = out.get("confidence", 1.0)
    if isinstance(conf, (int, float)) and conf < 0.3 and category not in ("unknown", "ambiguous", None):
        issues.append({
            "field":   "confidence",
            "problem": f"confidence {conf:.2f} below threshold 0.3",
        })

    # 7. Ambiguous category
    if category == "ambiguous":
        issues.append({"field": "category", "problem": "category is 'ambiguous' — cannot route to specific newsgroup"})

    # ── Determine recommended_action ─────────────────────────────────────────
    has_hallucination = any("hallucination" in i["problem"] for i in issues)
    has_schema_err    = any(i["field"] == "schema" for i in issues)
    has_inconsistency = any(
        i["field"] == "category" and "inconsistent" in i["problem"]
        for i in issues
    )
    has_rel_date      = any(i["field"] == "dates" for i in issues)
    has_ambiguous     = any("ambiguous" in i["problem"] for i in issues)
    has_low_conf      = any(i["field"] == "confidence" for i in issues)

    if not issues:
        action = "accept"
    elif has_hallucination:
        action = "fallback"          # re-extract from scratch
    elif has_ambiguous:
        action = "manual_review"
    elif has_schema_err or has_inconsistency:
        action = "repair"
    elif has_rel_date or has_low_conf:
        action = "export_with_warning"
    else:
        action = "export_with_warning"

    valid = (action in ("accept", "export_with_warning"))

    state.validation_result = {
        "valid":              valid,
        "schema_ok":          schema_res["valid"],
        "required_fields_ok": not has_schema_err,
        "issues":             issues,
        "recommended_action": action,
    }
    state.status = "validated"
    step_status  = "ok" if not issues else ("warning" if valid else "failed")
    state.log_step(
        "validate", step_status,
        issues_count=len(issues),
        action=action,
        checks=["schema", "hallucination", "consistency", "relative_date", "confidence", "ambiguous"],
    )
    return state


# ── Fallback / repair step ────────────────────────────────────────────────────

def _fallback_step(state: FlowState, action: str) -> FlowState:
    """
    Handle fallback according to *action*:

    repair         — fix schema / category issues in-place (no re-extraction)
    fallback       — rule-based re-extraction from scratch
    manual_review  — escalate; no further automatic action
    safe_failure   — return a structured null result
    """
    state.fallback_triggered = True
    text   = state.clean_text
    out    = dict(state.execute_output)
    issues = state.validation_result.get("issues", [])

    if action == "repair":
        repaired = dict(out)
        # Ensure all entity fields are proper lists (fix missing or wrong-type)
        for fld in ("persons", "organizations", "locations", "dates"):
            val = repaired.get(fld)
            if not isinstance(val, list):
                # Convert string to single-element list, otherwise empty list
                repaired[fld] = [val] if isinstance(val, str) and val else []
        # Fix category via keyword evidence
        if text:
            try:
                cls = classify_category(text)
                if not cls["is_ambiguous"] and cls["category"] not in ("unknown", "ambiguous"):
                    repaired["category"]   = cls["category"]
                    repaired["confidence"] = cls["confidence"]
                    repaired["scores"]     = cls["scores"]
            except Exception:
                pass
        # Mark relative-date cases for human review
        if any(i["field"] == "dates" for i in issues):
            repaired["needs_manual_review"] = True
        repaired["_repaired"] = True
        state.fallback_result   = repaired
        state.fallback_strategy = "schema_and_category_repair"

    elif action == "fallback":
        # Rule-based re-extraction from scratch
        try:
            if text:
                entities = extract_entities(text)
                cls      = classify_category(text)
            else:
                entities = {"persons": [], "organizations": [], "locations": [], "dates": []}
                cls      = {"category": "unknown", "confidence": 0.0, "scores": {}, "is_ambiguous": False}
            state.fallback_result = {
                "category":       cls["category"],
                "persons":        entities.get("persons", []),
                "organizations":  entities.get("organizations", []),
                "locations":      entities.get("locations", []),
                "dates":          entities.get("dates", []),
                "confidence":     cls["confidence"],
                "scores":         cls["scores"],
                "is_ambiguous":   cls.get("is_ambiguous", False),
                "_re_extracted":  True,
            }
            state.fallback_strategy = "rule_based_re_extraction"
        except Exception as exc:
            state.fallback_result = {
                "category":    "unknown",
                "persons":     [], "organizations": [], "locations": [], "dates": [],
                "confidence":  0.0, "scores":      {},
                "_re_extracted": True,
                "_error":      str(exc),
            }
            state.fallback_strategy = "safe_failure"
            state.add_error(f"fallback re-extraction failed: {exc}")

    elif action == "manual_review":
        state.fallback_result = {
            **out,
            "needs_manual_review": True,
            "_fallback_reason":    "ambiguous category — cannot resolve automatically",
        }
        state.fallback_strategy = "manual_review"

    elif action == "safe_failure":
        reason = state.execute_output.get("_reason", "safe failure")
        state.fallback_result = {
            "category":            None,
            "persons":             [], "organizations": [], "locations": [], "dates": [],
            "confidence":          0.0,
            "status":              "failed",
            "_reason":             reason,
            "needs_manual_review": True,
        }
        state.fallback_strategy = "safe_failure"

    state.log_step(
        "fallback", "ok",
        strategy=state.fallback_strategy,
        action=action,
    )
    return state


# ── NLP Flow Orchestrator ─────────────────────────────────────────────────────

class NLPFlow:
    """
    Stateful 5-stage NLP flow for 20 Newsgroups classification.

    Variant A — Classification:
      ingest text
      → route to classifier
      → execute classification + extraction
      → validate confidence / required output
      → export prediction + explanation
    """

    def run(
        self,
        text: str,
        case_id: str,
        pre_extracted: dict | None = None,
    ) -> FlowState:
        """
        Run the full flow for one case.

        Parameters
        ----------
        text          : raw input text
        case_id       : unique identifier for this case
        pre_extracted : optional dict injecting a pre-built extraction
                        (used in test scenarios for hallucination / wrong-category)

        Returns
        -------
        FlowState with all stages completed and export_output populated.
        """
        state = FlowState()

        # ── Stage 1: ingest ───────────────────────────────────────────────────
        state.case_id    = case_id
        state.raw_text   = text
        state.clean_text = text.strip()
        state.status     = "ingested"
        state.log_step(
            "ingest", "ok",
            raw_len=len(text),
            clean_len=len(state.clean_text),
            output_keys=["case_id", "raw_text", "clean_text"],
        )

        # ── Stage 2: route ────────────────────────────────────────────────────
        state = route_step(state)

        # ── Stage 3: execute ──────────────────────────────────────────────────
        state = execute_step(state, pre_extracted=pre_extracted)

        # ── Stage 4: validate ─────────────────────────────────────────────────
        state  = _validate_step(state)
        action = state.validation_result.get("recommended_action", "accept")

        # ── Stage 5a: handle validation verdict ───────────────────────────────
        if action == "accept":
            state.final_output = state.execute_output
            state.status       = "exported"

        elif action == "export_with_warning":
            state.final_output = state.execute_output
            for issue in state.validation_result.get("issues", []):
                state.add_warning(issue["problem"])
            state.status = "exported_with_warning"

        elif action == "safe_failure":
            state = _fallback_step(state, "safe_failure")
            state.final_output = state.fallback_result or {}
            state.status       = "failed"

        elif action == "manual_review":
            state = _fallback_step(state, "manual_review")
            state.final_output = state.fallback_result or state.execute_output
            state.add_warning("case escalated to manual review — ambiguous category")
            state.status = "manual_review"

        elif action in ("repair", "fallback"):
            # Attempt fix; then re-validate once
            state  = _fallback_step(state, action)
            repaired = state.fallback_result or {}

            # Temporarily swap execute_output for re-validation
            original_exec = state.execute_output
            state.execute_output = repaired
            state = _validate_step(state)
            re_action = state.validation_result.get("recommended_action", "accept")
            # Restore original (repaired now lives in fallback_result)
            state.execute_output = original_exec

            if re_action == "accept":
                state.final_output = repaired
                state.status       = "accepted_after_repair"
            elif re_action == "export_with_warning":
                state.final_output = repaired
                for issue in state.validation_result.get("issues", []):
                    state.add_warning(issue["problem"])
                state.status = "accepted_after_repair_with_warning"
            else:
                # Re-validation still failed — manual review
                state.final_output = repaired
                state.add_warning(
                    f"re-validation failed after {state.fallback_strategy} "
                    f"(action={re_action}) — escalating to manual review"
                )
                state.status = "manual_review"

        else:
            state.final_output = state.execute_output
            state.status       = "exported"

        # ── Stage 5b: export ──────────────────────────────────────────────────
        state = export_step(state)
        return state
