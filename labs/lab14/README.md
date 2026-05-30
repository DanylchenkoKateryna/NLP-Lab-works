# Lab 14 — Stateful NLP Flow: ingest → route → execute → validate → export

## 1. Use Case
**20 Newsgroups Classification Flow** (Variant A) — a stateful 5-stage pipeline
that processes newsgroup posts, classifies them into `sci.electronics`,
`soc.religion.christian`, or `alt.atheism`, and extracts named entities.

## 2. Flow Stages

```
Input text
    ↓
ingest   → case_id, raw_text, clean_text, status=ingested
    ↓
route    → route, schema_name, required_fields, routing_reason
    ↓
execute  → category, persons, orgs, locations, dates, confidence
    ↓
validate → schema, hallucinations, consistency, relative dates, confidence
    ↓
 ┌─────────────────────────────────────────────────────────────────┐
 │ accept              → status=exported                           │
 │ export_with_warning → status=exported_with_warning             │
 │ repair / fallback   → RepairFallback → re-validate             │
 │   re-validate ok    → status=accepted_after_repair[_with_warning]│
 │   re-validate fail  → status=manual_review                     │
 │ manual_review       → status=manual_review (no further agents) │
 │ safe_failure        → status=failed (structured null output)   │
 └─────────────────────────────────────────────────────────────────┘
    ↓
export   → JSON + Markdown + CSV
```

## 3. State Structure

`FlowState` dataclass threads through all stages:
- Identity: `case_id`, `raw_text`, `clean_text`
- Status lifecycle: `status`, `errors[]`, `warnings[]`
- Route: `route`, `schema_name`, `required_fields`, `routing_reason`, `keyword_scores`
- Execute: `execute_output`, `execute_method`
- Validate: `validation_result`
- Fallback: `fallback_triggered`, `fallback_result`, `fallback_strategy`
- Export: `final_output`, `export_output` (json + markdown + csv_row)
- Audit: `steps[]`

## 4. Supported Routes

| Route | Trigger |
|-------|---------|
| `electronics_deep` | sci.electronics keywords dominate |
| `religion_deep` | soc.religion.christian keywords dominate |
| `atheism_deep` | alt.atheism keywords dominate |
| `ambiguous_classification` | Keyword tie |
| `unknown_classification` | No keyword signal |
| `empty_input` | Empty text |

## 5. Validation Checks

1. Schema validity (required fields, correct types)
2. Hallucination detection (entity substring check in source text)
3. Category consistency (keyword rescore vs extracted category)
4. Relative-date detection (cannot normalize without reference date)
5. Confidence threshold (< 0.3 → warning)
6. Ambiguous category (→ manual review)

## 6. Fallback Logic

| Trigger | Strategy | Result |
|---------|----------|--------|
| Hallucination | `rule_based_re_extraction` | Re-extract from scratch |
| Schema error / wrong type / inconsistent category | `schema_and_category_repair` | Fix in-place |
| Ambiguous category | `manual_review` | Escalate |
| Empty input | `safe_failure` | Structured null |
| Relative date / low confidence | — | `export_with_warning` |

## 7. Export Format

Each case produces three simultaneous outputs:
- **JSON** — `{case_id, route, final_output, status, warnings, errors, …}`
- **Markdown** — human-readable report with entities, routing, warnings
- **CSV row** — 12-field single line for batch analysis

## 8. Running the Notebook

**Google Colab** (no setup needed):
1. Open `notebooks/lab14_flow_orchestration_crewai_flows.ipynb`
2. Click the Colab badge at the top
3. Runtime → Run all

**Local:**
```bash
cd repo-root
jupyter notebook notebooks/lab14_flow_orchestration_crewai_flows.ipynb
```

No additional packages — stdlib only.

## 9. Logs

- `docs/flow_logs_lab14.jsonl` — one JSON line per test case
- Generated automatically by the notebook (cell "Run 10 test cases + logging")

## 10. Metrics

| Metric | Value |
|--------|-------|
| Flow completion rate | 10/10 = 100% |
| Validation pass rate | 4/10 = 40% |
| Fallback activation rate | 6/10 = 60% |
| Fallback success rate | 4/6 ≈ 67% |
| Manual review / safe failure rate | 2/10 = 20% |
| Export valid rate | 10/10 = 100% |
| Avg steps per case | 6.1 |

## 11. Main Conclusion

The stateful flow's key advantage over an ad-hoc pipeline is **visible, controllable failure handling**:
- Hallucinations are caught and removed by fallback (case_005)
- Wrong categories are corrected before export (case_006, case_009)
- Schema errors (wrong field types) are repaired automatically (case_002)
- Ambiguous cases are escalated to manual review rather than silently mislabeled (case_007)
- Empty inputs produce structured safe-failures, not exceptions (case_010)

The overhead is not justified for simple, high-confidence cases (case_001, case_008)
where an ad-hoc pipeline would produce identical results in fewer steps.
