# Lab 13 — Multi-agent Crew: Triager → Extractor → Reviewer

## 1. Use Case
**20 Newsgroups Multi-agent Classifier** — structured extraction and classification from newsgroup posts using a 4-agent crew: Triager, Extractor, Reviewer, and Repair/Fallback.

## 2. Agents
| Agent | Role |
|-------|------|
| TriagerAgent | Routes input to extraction schema based on keyword evidence |
| ExtractorAgent | Extracts category + entities using `tools.py` |
| ReviewerAgent | Validates extraction — schema, consistency, hallucinations, dates |
| RepairAgent | Fixes specific reviewer-identified issues |
| FallbackHandler | Safe failure or rule-based re-extraction |

## 3. Workflow
```
Input text
    ↓
TriagerAgent  →  { task_type, route, difficulty, expected_fields }
    ↓
ExtractorAgent → { category, persons, orgs, locations, dates }
    ↓
ReviewerAgent  → { verdict, issues, recommended_action }
    ↓
 ┌──────────────────────────────────────────────────────────┐
 │ verdict=accept         → final output (accepted)         │
 │ verdict=repair_needed  → RepairAgent → re-review         │
 │   re-review accept     → accepted_after_repair           │
 │   re-review fail       → manual_review                   │
 │ verdict=fallback_needed → FallbackHandler → fallback     │
 │ verdict=manual_review  → manual_review (no agents)       │
 └──────────────────────────────────────────────────────────┘
```

## 4. Delegation Rules
1. Triager is always called first — sets the route for all downstream agents
2. Extractor is always called after Triager
3. Reviewer always checks Extractor output
4. RepairAgent is called only when `verdict == repair_needed`
5. FallbackHandler is called only when `verdict == fallback_needed`
6. After repair, Reviewer is called again (re-check)
7. If re-check still fails → `manual_review` (no more retries)

## 5. How Reviewer Works
The Reviewer performs five independent checks:
1. **Schema** — required fields: `category`, `persons`, `organizations`, `locations`, `dates`
2. **Category consistency** — re-runs keyword scorer on source text, compares to extracted category
3. **Hallucination** — checks if each extracted entity appears in the source text as a substring
4. **Completeness** — flags if text is long but all entity lists are empty
5. **Relative dates** — scans for expressions like "next month", "last week", etc.

## 6. How Fallback Works
| Trigger | Strategy |
|---------|----------|
| Hallucination found | Re-extract from scratch using `extract_entities` + `classify_category` |
| Empty input / extraction failed | Safe failure: structured error + partial output |
| Relative date | Mark `needs_manual_review=True` in repaired extraction |
| Ambiguous after repair | Escalate to manual_review |

## 7. Running the Notebook
**Google Colab** (no configuration needed):
1. Open `notebooks/lab13_multi_agent_crew_triager_extractor_reviewer.ipynb`
2. Click the Colab badge at the top
3. Runtime → Run all

**Local**:
```bash
cd repo-root
jupyter notebook notebooks/lab13_multi_agent_crew_triager_extractor_reviewer.ipynb
```

No additional packages required — all agents use Python stdlib only.

## 8. Logs
- `docs/crew_logs_lab13.jsonl` — one JSON line per test case, all agent outputs
- Generated automatically by the notebook (cell "Crew Logs")

## 9. Metrics
| Metric | Value |
|--------|-------|
| Valid final output rate | 9/10 = 90% |
| Reviewer catch rate | 6/6 = 100% |
| Fallback activation rate | 6/10 = 60% |
| Fallback success rate | 3/6 = 50% |
| Manual review rate | 2/10 = 20% |
| Avg agents per case | 4.0 |

Single-agent baseline accuracy: 6/10 = 60%  
Crew accuracy: 8/10 = 80% (crew correctly handles 2 additional cases)

## 10. Main Conclusion
The crew's key advantage over single-agent is **controlled failure handling**:
- Hallucinations are caught and cleaned by fallback (case_006)
- Wrong categories are corrected by repair (case_009)
- Ambiguous inputs are escalated to human review rather than silently wrong (cases 003, 010)
- Relative dates are flagged for human normalization (case_004)

The overhead is not worth it for simple, high-confidence inputs (cases 001, 005, 008) where the single agent would have worked fine.
