# Memory / Knowledge Policy — Lab 14

## 1. What Is Stored in State

`FlowState` holds only case-level data needed for the current processing run:

| Field | Purpose |
|-------|---------|
| `case_id` | Unique identifier for this run |
| `raw_text` | Original unmodified input |
| `clean_text` | Stripped text passed to tools |
| `route`, `schema_name`, `required_fields`, `routing_reason` | Routing decision and its justification |
| `keyword_scores` | Keyword hit counts per category (routing evidence) |
| `execute_output` | Tool outputs (category, entities, confidence) |
| `execute_method` | Which method was used (for audit) |
| `validation_result` | Issues, verdict, recommended action |
| `fallback_triggered`, `fallback_result`, `fallback_strategy` | Fallback decision and result |
| `final_output` | The accepted output (after repair if needed) |
| `export_output` | Serialised JSON + Markdown + CSV |
| `errors`, `warnings` | Non-blocking and blocking messages |
| `steps` | Ordered audit trail of all stage events |

## 2. What Is NOT Stored

The following are never placed in state or logs:

- API keys, tokens, or credentials
- Private user data beyond the input text itself
- Intermediate invalid (hallucinated / wrong) outputs accepted as ground truth
- Full large documents that are not needed by downstream stages
- Results from previous unrelated runs (state is created fresh per case)

## 3. Intermediate Outputs Between Stages

Allowed pass-through between stages:

| From → To | What passes |
|-----------|------------|
| ingest → route | `clean_text` |
| route → execute | `route`, `schema_name`, `required_fields` |
| execute → validate | `execute_output` (dict with category + entities) |
| validate → fallback | `validation_result.issues`, `recommended_action` |
| fallback → re-validate | `fallback_result` (swapped into `execute_output` temporarily) |
| final → export | `final_output`, `status`, `warnings`, `errors` |

**Rule:** each stage reads only the fields it needs from state and writes only its designated output fields.

## 4. Error Logging

- All stage errors are appended to `state.errors` as plain strings.
- Validation issues are recorded in `state.validation_result["issues"]` with field + problem description.
- Invalid intermediate outputs (e.g., hallucinated entities before fallback) are logged as issues, never accepted as truth.
- `state.steps` provides a full ordered audit trail: step name, status, key outputs.
- JSONL log (`flow_logs_lab14.jsonl`) contains one line per case with all of the above.

## 5. Knowledge / Schema Registry

Knowledge is **read-only** and lives outside state:

| Knowledge source | Location | Usage |
|-----------------|----------|-------|
| Keyword vocabularies (`_ELECTRONICS_KW`, etc.) | `src/tools.py` | Classification + consistency checks |
| Known entity lists (`KNOWN_PERSONS`, etc.) | `src/tools.py` | Entity extraction |
| Route → schema mapping (`_ROUTE_SCHEMA`) | `src/router.py` | Schema selection |
| Route → required fields (`_ROUTE_REQUIRED`) | `src/router.py` | Validation checks |
| Relative-date word sets | `src/flow.py` | Relative-date detection |

No stage can modify these knowledge sources. They are imported as module-level constants.

## 6. Read-Only Knowledge Files

The following are treated as read-only reference data:
- `src/tools.py` — keyword vocabularies and entity lists
- `src/router.py` — route and schema definitions
- `src/flow.py` — relative-date detection sets, validation thresholds

No flow stage writes back to these files.

## 7. Preventing State Pollution

- `FlowState` is created fresh for every `NLPFlow.run()` call — no shared mutable state between cases.
- Fallback re-extraction creates a new dict (`fallback_result`) and never overwrites `execute_output` permanently.
- Re-validation swaps `execute_output` temporarily and restores it after — original is preserved.
- Invalid intermediate results are stored only in `fallback_result` and flagged with `_repaired` / `_re_extracted` markers; they never become the accepted `final_output` unless re-validation passes.

## 8. Data That Must Not Be Logged

- API keys or authentication credentials (none are used in this implementation)
- Passwords or private credentials
- Personally identifiable information beyond what is in the test input texts
- Raw hallucinated outputs presented as verified ground truth
