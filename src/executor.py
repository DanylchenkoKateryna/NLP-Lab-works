"""
executor.py — Execute step for Lab 14 NLP flow.

Runs the appropriate NLP action for the route chosen by route_step.
For Variant A (Classification), the execute action is always:
  extract_entities + classify_category from tools.py.

If pre_extracted is supplied (testing / hallucination simulation),
it is used instead of running the tools.

Knowledge (read-only)
---------------------
KNOWN_PERSONS, KNOWN_ORGS, KNOWN_LOCATIONS, keyword vocabularies — all
live in tools.py and are not modified by this step.
"""
from __future__ import annotations

try:
    from tools import extract_entities, classify_category
    from flow_state import FlowState
    from router import ROUTE_EMPTY
except ImportError:
    from src.tools import extract_entities, classify_category
    from src.flow_state import FlowState
    from src.router import ROUTE_EMPTY


def execute_step(
    state: FlowState,
    pre_extracted: dict | None = None,
) -> FlowState:
    """
    Execute NLP extraction + classification according to state.route.

    Parameters
    ----------
    state         : current FlowState (must be in 'routed' status)
    pre_extracted : optional dict to inject instead of running tools
                    (used for testing hallucinations / wrong-category scenarios)

    Updates
    -------
    state.execute_output, state.execute_method, state.execute_error,
    state.status.
    """
    # Empty input — nothing to run
    if state.route == ROUTE_EMPTY:
        state.execute_output = {
            "category":           None,
            "persons":            [],
            "organizations":      [],
            "locations":          [],
            "dates":              [],
            "confidence":         0.0,
            "scores":             {},
            "_extraction_failed": True,
            "_reason":            "empty input — no text to process",
        }
        state.execute_method = "skipped (empty input)"
        state.status         = "executed"
        state.log_step("execute", "skipped", reason="empty input")
        return state

    text = state.clean_text

    # ── Simulated / pre-supplied extraction ───────────────────────────────────
    if pre_extracted is not None:
        output = dict(pre_extracted)
        # Ensure all entity fields exist (may be missing in injected dicts)
        for key in ("persons", "organizations", "locations", "dates"):
            output.setdefault(key, [])
        if "category" not in output:
            output["category"] = "unknown"
        if "confidence" not in output:
            try:
                cls = classify_category(text)
                output["confidence"]   = cls["confidence"]
                output["scores"]       = cls["scores"]
                output["is_ambiguous"] = cls["is_ambiguous"]
            except Exception:
                output["confidence"] = 0.0
                output["scores"]     = {}
        method = "pre_extracted (simulated injection)"

    # ── Live tool execution ───────────────────────────────────────────────────
    else:
        try:
            entities = extract_entities(text)
            cls      = classify_category(text)
            output = {
                "category":      cls["category"],
                "persons":       entities["persons"],
                "organizations": entities["organizations"],
                "locations":     entities["locations"],
                "dates":         entities["dates"],
                "confidence":    cls["confidence"],
                "scores":        cls["scores"],
                "is_ambiguous":  cls["is_ambiguous"],
            }
            method = "extract_entities + classify_category"
        except Exception as exc:
            state.execute_output = {
                "category":           "unknown",
                "persons":            [],
                "organizations":      [],
                "locations":          [],
                "dates":              [],
                "confidence":         0.0,
                "scores":             {},
                "_extraction_failed": True,
                "_reason":            str(exc),
            }
            state.execute_error  = str(exc)
            state.execute_method = "failed"
            state.status         = "executed"
            state.add_error(f"execute failed: {exc}")
            state.log_step("execute", "error", error=str(exc))
            return state

    state.execute_output = output
    state.execute_method = method
    state.status         = "executed"
    state.log_step(
        "execute", "ok",
        method=method,
        category=output.get("category"),
        confidence=output.get("confidence"),
        entity_count=sum(
            len(output.get(f, []))
            for f in ("persons", "organizations", "locations", "dates")
        ),
    )
    return state
