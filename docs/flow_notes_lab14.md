# Flow Notes — Lab 14: Stateful NLP Flow

## 1. Use Case
**20 Newsgroups Classification Flow** (Variant A) — a stateful 5-stage pipeline
that processes newsgroup posts through explicit ingest → route → execute →
validate → export stages.  Continues Variant A from ЛР12/ЛР13, but replaces
the multi-agent crew with a single orchestrated flow that owns state,
transitions, and fallback decisions.

## 2. Stages of the Flow

| Stage    | Responsibility |
|----------|---------------|
| ingest   | Accept raw text, create case_id, strip clean_text, initialise state |
| route    | Keyword-score text → choose route, schema, required fields |
| execute  | Call `extract_entities` + `classify_category` from tools.py |
| validate | Check schema, hallucinations, category consistency, relative dates, confidence |
| export   | Produce JSON + Markdown + CSV row from final_output |

## 3. State Structure

```python
@dataclass
class FlowState:
    # Identity
    case_id:    str
    raw_text:   str
    clean_text: str
    # Status lifecycle
    status:   str       # ingested | routed | executed | validated | exported | …
    errors:   list[str]
    warnings: list[str]
    # Route
    route:           str   # e.g. "electronics_deep"
    schema_name:     str
    required_fields: list[str]
    routing_reason:  str
    keyword_scores:  dict
    # Execute
    execute_output:  dict
    execute_method:  str
    # Validate
    validation_result: dict
    # Fallback
    fallback_triggered: bool
    fallback_result:    dict | None
    fallback_strategy:  str
    # Export
    final_output:  dict
    export_output: dict   # {json, markdown, csv_row, csv_header}
    # Audit
    steps: list[dict]
```

## 4. Possible Routes

| Route                   | Trigger condition |
|-------------------------|-------------------|
| `electronics_deep`      | sci.electronics keywords dominate |
| `religion_deep`         | soc.religion.christian keywords dominate |
| `atheism_deep`          | alt.atheism keywords dominate |
| `ambiguous_classification` | Keyword tie between top-2 categories |
| `unknown_classification`   | No keyword signal (all scores = 0) |
| `empty_input`           | Text is empty after stripping |

Each route maps to a schema and required-field list used by validate.

## 5. What execute Does

- Calls `extract_entities(text)` → persons, organizations, locations, dates
- Calls `classify_category(text)` → category, confidence, scores
- If `pre_extracted` is supplied, uses it directly (test simulation)
- On `empty_input` route: marks `_extraction_failed=True`, skips tools

## 6. What validate Checks

1. **Schema validity** — `validate_extraction()` from tools.py; also surfaces its warnings as soft issues
2. **Hallucination detection** — entity substring check in source text
3. **Category consistency** — re-run `classify_category`, compare with extracted category
4. **Relative-date detection** — unigrams (tomorrow, yesterday…) and bigrams (next month, last week…)
5. **Confidence threshold** — flags if confidence < 0.3 and category is not unknown/ambiguous
6. **Ambiguous category** — always escalates to manual_review

## 7. When Fallback Triggers

| Trigger | Strategy | Outcome |
|---------|----------|---------|
| Hallucination found | `rule_based_re_extraction` | Re-extract with tools from scratch |
| Ambiguous category | `manual_review` | No further automatic action |
| Schema error / wrong type / inconsistent category | `schema_and_category_repair` | Fix in-place + re-validate |
| Relative date / low confidence | — | `export_with_warning` (no fallback) |
| Empty input | `safe_failure` | Structured null result |

## 8. Export Format

Three simultaneous formats produced per case:

- **JSON** — structured dict with case_id, route, final_output, status, warnings, errors
- **Markdown** — human-readable report (# Flow Export — case_id, entities, routing, warnings)
- **CSV row** — single line with 12 fields; header available as `csv_header`

Export is always stable — even a `failed` case produces a structured dict, not an exception.

## 9. What Flow Improved vs Ad-hoc Pipeline

| Problem | Ad-hoc pipeline | Stateful flow |
|---------|----------------|---------------|
| Hallucinated entity | Accepted silently | Validator catches → re-extraction removes it |
| Wrong category | Returns unchecked | Validator flags inconsistency → repair corrects |
| Missing/wrong-type field | Silently skipped | Schema check detects → repair normalises |
| Relative date | Ignored | Detected → flagged in warning, marked needs_manual_review |
| Empty input | Exception or silent error | Structured safe-failure with reason |
| Ambiguous category | Picks wrong winner | Escalated to manual review explicitly |
| Debugging | No visibility into failure point | Step log pinpoints which stage failed and why |

Flow correctly handles 8/10 cases automatically; ad-hoc handles 4/10 correctly.

## 10. Where Flow Was Excessive

- **case_001** (clear electronics): three extra validation checks add no value — single tool call would suffice.
- **case_008** (noisy keyword list): routing overhead is not needed for pure-keyword text.
- **case_003** (unknown category): validation warning and export_with_warning add latency with little benefit for genuinely signal-free text.
- For short, high-confidence, single-category texts, the stateful overhead (6+ steps) is disproportionate.

## 11. What Would Be Fixed Next

1. Add fuzzy entity matching (rapidfuzz) to handle typos in entity lookup
2. Add LLM-based disambiguation for `ambiguous_classification` route
3. Separate FallbackHandler re-extraction from Executor logic (currently identical tools)
4. Add per-route confidence thresholds (electronics vs religion may need different thresholds)
5. Add unit tests per stage to verify validate catches specific hallucination patterns
