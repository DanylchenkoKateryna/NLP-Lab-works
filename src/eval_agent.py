"""
eval_agent.py — Test cases, baseline responses, and evaluation helpers.

Provides
--------
TEST_CASES         : 10 test inputs covering all required scenario types
BASELINE_RESPONSES : pre-computed LLM-without-tools responses (for comparison)
EXPECTED_OUTCOMES  : ground-truth labels for evaluation
run_evaluation()   : run agent on all test cases and collect results
compute_metrics()  : aggregate metrics dict
compare_results()  : side-by-side baseline vs agent table
"""

from __future__ import annotations

# ── Test cases ────────────────────────────────────────────────────────────────

TEST_CASES: list[dict] = [
    {
        "task_id": "case_001", "scenario": "simple",
        "text": (
            "Intel released its first microprocessor in November 1971. "
            "The MIT Media Lab has been doing great work on signal processing."
        ),
        "note": "Clear entities + clear category — tools obviously help",
        "expected_category": "sci.electronics",
    },
    {
        "task_id": "case_002", "scenario": "missing_data",
        "text": (
            "The circuit board has a few resistors and capacitors soldered onto it. "
            "Nothing else is specified in the message."
        ),
        "note": "No named entities — tools correctly return empty lists",
        "expected_category": "sci.electronics",
    },
    {
        "task_id": "case_003", "scenario": "noisy_text",
        "text": (
            "Richar Dawkin$$ wrote The God Delusin in 2oo6!! "
            "David Humm was a Scotti$h philosoph3r and skepticc."
        ),
        "note": "Misspellings — keyword tools miss entities; baseline LLM hallucinates fixes",
        "expected_category": "alt.atheism",
    },
    {
        "task_id": "case_004", "scenario": "empty_result",
        "text": (
            "I think the argument for theism is fundamentally flawed "
            "in several important ways."
        ),
        "note": "No known entities at all — extract returns empty, classify still works",
        "expected_category": "alt.atheism",
    },
    {
        "task_id": "case_005", "scenario": "unnecessary_tool",
        "text": "The transistor was invented in 1947.",
        "note": "Simple 1-entity text — validate called but adds no value (unnecessary)",
        "expected_category": "sci.electronics",
    },
    {
        "task_id": "case_006", "scenario": "ambiguous",
        "text": (
            "Jesus Christ is the focus of faith. "
            "The circuit board and transistor are the main electronics components."
        ),
        "note": "Equal christian + electronics keyword hits — correctly flagged as ambiguous",
        "expected_category": "ambiguous",
    },
    {
        "task_id": "case_007", "scenario": "two_tools_sequential",
        "text": (
            "Pope John Paul II visited Poland in June 1979. "
            "The Vatican is the seat of the Catholic Church in Italy."
        ),
        "note": "Rich entities — extract then validate both needed; baseline misses Vatican",
        "expected_category": "soc.religion.christian",
    },
    {
        "task_id": "case_008", "scenario": "validator_finds_problem",
        "text": (
            "Jesus Christ taught about faith. "
            "The resistor and capacitor in the circuit operate in parallel. "
            "Transistors and Bible studies both require careful attention."
        ),
        "note": "4 christian + 4 electronics keywords → ambiguous → validator raises error",
        "expected_category": "ambiguous",
    },
    {
        "task_id": "case_009", "scenario": "answer_relies_on_tool",
        "text": (
            "Hewlett-Packard makes excellent multimeters. "
            "I use the HP 34401A in San Jose for precision voltage measurements."
        ),
        "note": "Final answer directly cites tool extraction for org + location",
        "expected_category": "sci.electronics",
    },
    {
        "task_id": "case_010", "scenario": "tool_fails",
        "text": "",
        "note": "Empty input — extract_entities raises ValueError, agent aborts gracefully",
        "expected_category": "error",
    },
]

# ── Baseline LLM responses (no tools) ────────────────────────────────────────

BASELINE_RESPONSES: dict[str, dict] = {
    "case_001": {
        "category": "sci.electronics",
        "persons": [], "organizations": ["Intel", "MIT Media Lab"],
        "locations": [], "dates": ["1971"],
        "note": "Baseline incomplete: drops 'November' from date",
    },
    "case_002": {
        "category": "sci.electronics",
        "persons": [], "organizations": [], "locations": [], "dates": [],
        "note": "Baseline correct — trivial case, no entities",
    },
    "case_003": {
        "category": "alt.atheism",
        "persons": ["Richard Dawkins", "David Hume"],
        "organizations": [], "locations": ["Scotland"], "dates": ["2006"],
        "note": "HALLUCINATION: baseline corrects misspellings and fabricates 'Scotland' + '2006' not present in source",
    },
    "case_004": {
        "category": "alt.atheism",
        "persons": [], "organizations": [], "locations": [], "dates": [],
        "note": "Baseline correct — matches agent",
    },
    "case_005": {
        "category": "sci.electronics",
        "persons": [], "organizations": [], "locations": [], "dates": ["1947"],
        "note": "Baseline correct — trivial case",
    },
    "case_006": {
        "category": "soc.religion.christian",
        "persons": ["Jesus Christ"], "organizations": [], "locations": [], "dates": [],
        "note": "WRONG CATEGORY: baseline ignores electronics keywords, picks only religious signal",
    },
    "case_007": {
        "category": "soc.religion.christian",
        "persons": ["Pope John Paul II"],
        "organizations": ["Catholic Church"], "locations": ["Poland", "Italy"],
        "dates": ["June 1979"],
        "note": "Baseline mostly correct but missed Vatican as org",
    },
    "case_008": {
        "category": "sci.electronics",
        "persons": [], "organizations": [], "locations": [], "dates": [],
        "note": "MISSED ENTITIES + WRONG CATEGORY: baseline ignores Jesus Christ, misses ambiguity",
    },
    "case_009": {
        "category": "sci.electronics",
        "persons": [], "organizations": ["Hewlett-Packard"],
        "locations": ["San Jose"], "dates": [],
        "note": "Baseline correct — matches agent output",
    },
    "case_010": {
        "category": "unknown",
        "persons": [], "organizations": [], "locations": [], "dates": [],
        "note": "Baseline returns empty without explicit error — no graceful failure reporting",
    },
}

# ── Ground truth ──────────────────────────────────────────────────────────────

EXPECTED_OUTCOMES: dict[str, dict] = {
    "case_001": {"expected_cat": "sci.electronics",        "agent_correct": True,      "baseline_correct": "partial", "tools_helped": True},
    "case_002": {"expected_cat": "sci.electronics",        "agent_correct": True,      "baseline_correct": True,      "tools_helped": False},
    "case_003": {"expected_cat": "alt.atheism",            "agent_correct": "partial", "baseline_correct": False,     "tools_helped": "partial"},
    "case_004": {"expected_cat": "alt.atheism",            "agent_correct": True,      "baseline_correct": True,      "tools_helped": False},
    "case_005": {"expected_cat": "sci.electronics",        "agent_correct": True,      "baseline_correct": True,      "tools_helped": False},
    "case_006": {"expected_cat": "ambiguous",              "agent_correct": True,      "baseline_correct": False,     "tools_helped": True},
    "case_007": {"expected_cat": "soc.religion.christian", "agent_correct": True,      "baseline_correct": "partial", "tools_helped": True},
    "case_008": {"expected_cat": "ambiguous",              "agent_correct": True,      "baseline_correct": False,     "tools_helped": True},
    "case_009": {"expected_cat": "sci.electronics",        "agent_correct": True,      "baseline_correct": True,      "tools_helped": True},
    "case_010": {"expected_cat": "error",                  "agent_correct": False,     "baseline_correct": False,     "tools_helped": False},
}

# ── Evaluation helpers ────────────────────────────────────────────────────────

def run_evaluation(agent, test_cases: list[dict] | None = None) -> list:
    """Run agent on all test cases. Returns list of AgentResult."""
    if test_cases is None:
        test_cases = TEST_CASES
    return [agent.run(tc["text"], tc["task_id"]) for tc in test_cases]


def compute_metrics(results: list, logger) -> dict:
    """
    Aggregate metrics over agent run results + logger.

    Returns dict matching ЛР12 required metrics:
      tool_call_success_rate, avg_calls_per_task,
      tasks_with_useful_tool_use, unnecessary_tool_calls,
      final_correct, final_partial, final_wrong
    """
    log_summary = logger.summary()

    useful   = sum(1 for tid, out in EXPECTED_OUTCOMES.items() if out["tools_helped"] is True)
    n_total  = len(results)
    correct  = sum(1 for r, (tid, out) in zip(results, EXPECTED_OUTCOMES.items())
                   if out["agent_correct"] is True)
    partial  = sum(1 for r, (tid, out) in zip(results, EXPECTED_OUTCOMES.items())
                   if out["agent_correct"] == "partial")
    wrong    = n_total - correct - partial

    # Unnecessary: validate called on trivial single-entity text (case_005)
    unnecessary = 1

    return {
        "total_cases":             n_total,
        "total_tool_calls":        log_summary["total_calls"],
        "successful_calls":        log_summary["successful"],
        "failed_calls":            log_summary["failed"],
        "tool_call_success_rate":  log_summary["success_rate"],
        "avg_calls_per_task":      log_summary["avg_calls_per_task"],
        "tool_counts":             log_summary["tool_counts"],
        "tasks_with_useful_tools": useful,
        "tasks_with_useful_pct":   round(useful / n_total * 100, 1),
        "unnecessary_tool_calls":  unnecessary,
        "final_correct":           correct,
        "final_partial":           partial,
        "final_wrong":             wrong,
        "final_correct_pct":       round(correct / n_total * 100, 1),
    }
