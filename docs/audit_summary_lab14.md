# Audit Summary — Lab 14: Stateful NLP Flow

## 1. Use Case
**20 Newsgroups Classification Flow** (Variant A).  
A stateful 5-stage NLP pipeline that classifies newsgroup posts into
`sci.electronics`, `soc.religion.christian`, or `alt.atheism` and extracts
named entities, with explicit routing, validation, fallback, and structured export.

## 2. Stages Implemented
ingest → route → execute → validate → export

All 5 stages are implemented.  Fallback logic sits between validate and export.

## 3. Test Cases
10 test cases covering all required scenario types:
simple, missing_required_field, unknown_route, validation_catches,
fallback_needed, fallback_helps, fallback_doesnt_help, noisy_input,
ambiguous_route, manual_review_safe_failure.

## 4. Flow Completion Rate
**10/10 = 100%** — every case reaches the export stage (even failures produce a structured output).

## 5. Validation Pass Rate
**4/10 = 40%** — 4 cases validated without triggering fallback:
case_001 (simple), case_003 (unknown, warning), case_004 (relative date, warning), case_008 (noisy input).

## 6. Fallback Activation Rate
**6/10 = 60%** — fallback triggered in:
case_002 (schema repair), case_005 (hallucination re-extraction),
case_006 (wrong category repair), case_007 (ambiguous → manual review),
case_009 (wrong category repair), case_010 (safe failure).

## 7. Fallback Success Rate
**4/6 ≈ 67%** — fallback successfully resolved 4 cases:
case_002 (schema repaired), case_005 (hallucination removed), case_006 (category corrected), case_009 (category corrected).  
Failed in case_007 (ambiguity unresolvable) and case_010 (empty input → structured failure).

## 8. Export Valid Rate
**10/10 = 100%** — all cases produce a structured JSON export with `final_output` present.

## 9. Manual Review / Safe Failure Rate
**2/10 = 20%** — case_007 (manual_review) and case_010 (failed / safe failure).

## 10. Best Flow Examples

**case_005 — Hallucination caught and cleaned**  
Injected `Hewlett-Packard` into electronics text where HP does not appear.  
Validator detected hallucination → fallback re-extracted from scratch → HP removed → accepted_after_repair.  
*Key benefit: ad-hoc pipeline would have silently accepted the hallucinated entity.*

**case_006 — Wrong category corrected**  
Pre-extracted with `soc.religion.christian` for a clear Dawkins/atheism text.  
Validator detected inconsistency via keyword rescoring → repair corrected to `alt.atheism` → accepted_after_repair.  
*Key benefit: systematic category error caught at validate stage, not silently propagated.*

**case_009 — Religion text with injected wrong category**  
Pre-extracted `alt.atheism` for Pope/Poland/Catholic Church text.  
Repair corrected to `soc.religion.christian` → accepted_after_repair.

## 11. Problematic Examples

**case_007 — Fallback did not help**  
Ambiguous text (christian=electronics tie) + injected hallucination.  
Fallback re-extracted but text is genuinely ambiguous → re-extraction also returns `ambiguous` → manual_review.  
*Root cause: ambiguity is inherent to the text; no rule-based tool can resolve it.*

**case_010 — Empty input**  
Empty string → route=empty_input → execute marks `_extraction_failed` → validate → safe_failure.  
Final output is a structured null dict with `status=failed` and `needs_manual_review=True`.  
*Design decision: structured failure is preferable to raising an exception.*

**case_003 — Unknown category**  
Philosophy text with no newsgroup keywords → `unknown_classification` → category=unknown.  
Exported with warning about empty entities and unknown category.  
The flow adds overhead (6 steps) for a case that provides no extractable signal.

## 12. What Flow Improved vs Ad-hoc Pipeline

| Scenario | Ad-hoc | Stateful flow |
|----------|--------|---------------|
| Hallucination | Accepted silently | Caught + removed |
| Wrong category | Not detected | Caught + corrected |
| Schema error (wrong type) | Ignored or crash | Detected + repaired |
| Relative date | Ignored | Flagged + warning |
| Ambiguous result | Picks wrong winner | Explicit manual_review |
| Empty input | Exception | Structured safe-failure |
| Debugging | No visibility | Step-by-step audit trail |

Ad-hoc accuracy: 4/10 (40%).  Flow accuracy: 8/10 (80%).

## 13. What Would Be Improved Next
1. LLM-based disambiguation for `ambiguous_classification` route (e.g., GPT-4o-mini)
2. Fuzzy entity matching (rapidfuzz) to handle slight name variations
3. Differentiated fallback strategies per route (religion and electronics may need different re-extraction hints)
4. Per-route confidence thresholds (not a single 0.3 for all categories)
5. Unit tests per stage isolating validate, repair, re-validate logic
6. Batch mode with parallel case processing for large datasets
