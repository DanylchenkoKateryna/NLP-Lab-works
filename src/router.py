"""
router.py — Route step for Lab 14 NLP flow.

Determines the pipeline route from the cleaned input text using
keyword scoring (classify_category from tools.py).

Routes
------
electronics_deep        — sci.electronics dominant
religion_deep           — soc.religion.christian dominant
atheism_deep            — alt.atheism dominant
ambiguous_classification — keyword tie (two or more categories tied)
unknown_classification  — no keyword signal at all
empty_input             — text is empty after stripping

Knowledge (read-only)
---------------------
Route → schema and required-field definitions are static constants.
The keyword vocabulary lives in tools.py and is never modified by this step.
"""
from __future__ import annotations

try:
    from tools import classify_category
    from flow_state import FlowState
except ImportError:
    from src.tools import classify_category
    from src.flow_state import FlowState


# ── Route name constants ──────────────────────────────────────────────────────

ROUTE_ELECTRONICS = "electronics_deep"
ROUTE_RELIGION    = "religion_deep"
ROUTE_ATHEISM     = "atheism_deep"
ROUTE_AMBIGUOUS   = "ambiguous_classification"
ROUTE_UNKNOWN     = "unknown_classification"
ROUTE_EMPTY       = "empty_input"


# ── Knowledge: schema + required fields per route ────────────────────────────

_ROUTE_SCHEMA: dict[str, str] = {
    ROUTE_ELECTRONICS: "electronics_schema",
    ROUTE_RELIGION:    "christian_schema",
    ROUTE_ATHEISM:     "atheism_schema",
    ROUTE_AMBIGUOUS:   "mixed_schema",
    ROUTE_UNKNOWN:     "generic_schema",
    ROUTE_EMPTY:       "empty_schema",
}

_ROUTE_REQUIRED: dict[str, list[str]] = {
    ROUTE_ELECTRONICS: ["category", "organizations", "dates"],
    ROUTE_RELIGION:    ["category", "persons", "locations"],
    ROUTE_ATHEISM:     ["category", "persons", "dates"],
    ROUTE_AMBIGUOUS:   ["category"],
    ROUTE_UNKNOWN:     ["category"],
    ROUTE_EMPTY:       [],
}


# ── Route step ────────────────────────────────────────────────────────────────

def route_step(state: FlowState) -> FlowState:
    """
    Determine route from state.clean_text.

    Updates
    -------
    state.route, state.schema_name, state.required_fields,
    state.routing_reason, state.keyword_scores, state.status.

    Does NOT perform extraction or classification — only routing.
    """
    text = state.clean_text

    # Empty-input shortcut
    if not text:
        _set_route(state, ROUTE_EMPTY, {}, "input is empty after stripping")
        return state

    # Keyword scoring via tools.py (read-only knowledge)
    cls    = classify_category(text)
    scores = cls["scores"]

    if cls["category"] == "unknown":
        reason = "no keyword signal found for any category"
        route  = ROUTE_UNKNOWN

    elif cls["is_ambiguous"]:
        top_val = max(scores.values())
        tied    = [k for k, v in scores.items() if v == top_val]
        reason  = "keyword tie: " + ", ".join(f"{k}={v}" for k, v in scores.items() if v == top_val)
        route   = ROUTE_AMBIGUOUS

    elif cls["category"] == "sci.electronics":
        route  = ROUTE_ELECTRONICS
        reason = f"electronics keywords dominate (score={scores['sci.electronics']})"

    elif cls["category"] == "soc.religion.christian":
        route  = ROUTE_RELIGION
        reason = f"christian keywords dominate (score={scores['soc.religion.christian']})"

    else:  # alt.atheism
        route  = ROUTE_ATHEISM
        reason = f"atheism keywords dominate (score={scores['alt.atheism']})"

    _set_route(state, route, scores, reason)
    return state


def _set_route(
    state: FlowState,
    route: str,
    scores: dict,
    reason: str,
) -> None:
    state.route           = route
    state.schema_name     = _ROUTE_SCHEMA[route]
    state.required_fields = _ROUTE_REQUIRED[route]
    state.routing_reason  = reason
    state.keyword_scores  = scores
    state.status          = "routed"
    state.log_step(
        "route", "ok",
        route=route,
        schema=state.schema_name,
        required_fields=state.required_fields,
        reason=reason,
        scores=scores,
    )
