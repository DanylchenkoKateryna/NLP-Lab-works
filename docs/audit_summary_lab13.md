# Audit Summary - Lab 13: Multi-agent Crew

**Date:** 2026-05-30

## 1. Use Case
Multi-agent crew for 20 Newsgroups post classification and entity extraction.
Extends single-agent pipeline (LR12) with routing, review, repair, and fallback.

## 2. Agents Implemented
- TriagerAgent   - keyword-based routing
- ExtractorAgent - extraction via tools.py
- ReviewerAgent  - schema/consistency/hallucination/date checks
- RepairAgent    - targeted fixes
- FallbackHandler - re-extraction or safe failure

## 3. Test Cases
10 cases: simple, missing_required_field, ambiguous_entity, relative_date,
hallucination_prone, simulated_hallucination, fallback_needed,
reviewer_rejects_then_accepts, repair_helps, repair_fails_manual.

## 4. Valid Final Output Rate: 9/10 = 90.0%

## 5. Reviewer Catch Rate: 6/6 = 100.0%

## 6. Fallback Activation Rate: 6/10 = 60.0%

## 7. Fallback Success Rate: 3/6 = 50.0%

## 8. Manual Review Rate: 2/10 = 20.0%

## 9. Single-agent vs Crew
| Metric | Baseline | Crew |
|--------|----------|------|
| Valid output | 6/10 | 9/10 |
| Hallucinations caught | 0 | 1 |
| Wrong category corrected | 0 | 1 |
| Ambiguous escalated correctly | 0 | 2 |
| Relative dates flagged | 0 | 1 |

## 10. Best Examples
- case_006: HP hallucination caught by Reviewer, cleaned by FallbackHandler
- case_009: wrong category corrected by RepairAgent
- case_004: relative dates flagged, repair marks needs_manual_review

## 11. Problematic Examples
- case_003/010: ambiguity unresolvable without LLM -> correct manual_review escalation
- case_007: empty input -> structured safe failure

## 12. Next Steps
1. LLM-based disambiguation for ambiguous cases
2. Fuzzy entity matching for typos
3. Confidence threshold check in Reviewer (e.g., flag if conf < 0.4)
4. Differentiate FallbackHandler strategies from Extractor logic
5. Add unit tests per agent