# Crew Notes — Lab 13: Multi-agent Crew

## 1. Use Case
**20 Newsgroups Multi-agent Classifier** — structured extraction + classification from newsgroup posts using a crew of 3–4 agents. Extends ЛР12's single-agent pipeline by adding routing, multi-stage review, and fallback.

## 2. Agents in Crew
| Agent | File | Role |
|-------|------|------|
| TriagerAgent | `src/agents.py` | Routes input, selects extraction schema |
| ExtractorAgent | `src/agents.py` | Structured extraction using tools |
| ReviewerAgent | `src/reviewer.py` | Validates extraction, issues verdict |
| RepairAgent | `src/fallback.py` | Targeted repair of specific issues |
| FallbackHandler | `src/fallback.py` | Safe failure or rule-based re-extraction |

## 3. Role of Each Agent

### TriagerAgent
- Reads input text, counts keyword evidence per category
- Selects route: `electronics_schema`, `religious_schema`, `atheism_schema`, `mixed_schema`
- Assigns difficulty: easy / medium / hard
- Does NOT extract entities

### ExtractorAgent
- Calls `extract_entities()` and `classify_category()` from tools.py
- Follows the route and expected schema from Triager
- Accepts pre_extracted for testing/simulation
- Returns structured dict with category, persons, orgs, locations, dates

### ReviewerAgent
- Checks schema validity (all required fields present)
- Checks category consistency (re-run keyword scorer, compare result)
- Detects hallucinations (entity not found as substring in source text)
- Detects relative dates (flags for manual normalization)
- Issues one of four verdicts: accept / repair_needed / fallback_needed / manual_review

### RepairAgent
- Removes hallucinated entities
- Fixes wrong category based on keyword evidence
- Attempts to resolve ambiguous category via tie-breaking
- Marks `needs_manual_review=True` when it cannot fully fix
- Sets `_repaired=True` so re-review knows repair was attempted

### FallbackHandler
- Strategy 1: rule-based re-extraction from scratch (extract_entities + classify_category)
- Strategy 2: safe failure — returns partial output + structured error

## 4. Delegation Rules
```
Triager  → always first
Extractor → always after Triager
Reviewer  → always checks Extractor output

if verdict == accept:
    → done

if verdict == repair_needed:
    → RepairAgent
    → Reviewer (re-check)
    → if re-review == accept: accepted_after_repair
    → else: manual_review

if verdict == fallback_needed:
    → FallbackHandler → fallback

if verdict == manual_review:
    → manual_review (no further agents)
```

## 5. What Reviewer Checks
1. **Schema validity** — all five required fields present (category, persons, organizations, locations, dates); list fields are actually lists
2. **Category consistency** — re-run keyword scoring on text; compare top category to extracted category; flag if they differ or if tie is not marked "ambiguous"
3. **Hallucination detection** — for each entity in persons/organizations/locations, check if it appears (case-insensitive) as a substring in the source text
4. **Completeness** — if text has 15+ words but all entity lists are empty, flag
5. **Relative dates** — scan text for relative temporal expressions (next month, last week, etc.) and flag for normalization

## 6. When Fallback Triggers
| Trigger | Action |
|---------|--------|
| Hallucination detected | `fallback_needed` → FallbackHandler re-extracts from scratch |
| Empty/failed extraction | `fallback_needed` → FallbackHandler safe failure |
| Schema error | `repair_needed` → RepairAgent fills missing fields |
| Wrong category | `repair_needed` → RepairAgent corrects via keyword evidence |
| Ambiguous category | `repair_needed` → RepairAgent tries to resolve; if still tied → `manual_review` |
| Relative date | `repair_needed` → RepairAgent marks `needs_manual_review=True` → re-review accepts |

## 7. What Crew Improved vs Single-agent
| Issue | Single agent | Crew |
|-------|-------------|------|
| Hallucination | Accepted silently | Reviewer catches → fallback removes |
| Ambiguous category | Picks wrong winner | Detects tie → repair → manual_review |
| Wrong category | Returns unchecked | Reviewer flags → repair corrects |
| Relative dates | Ignored | Flagged and marked |
| Extraction failure | Silent error | Structured safe failure + reason |

Crew correctly routes 8/10 cases; single-agent baseline is correct on only 6/10.

## 8. Where Multi-agent Was Excessive
- **case_001 (simple)**: All 3 agents called; reviewer adds no value — tools + single agent would suffice
- **case_002 (no signal)**: ReviewerAgent checks consistency on "unknown" category — adds latency with zero benefit
- **case_005 (short text)**: Same as case_001; Triager overhead not worth it for 5-word inputs
- For texts with strong unambiguous signal, the Triager's routing step is redundant since the Extractor would produce a correct result anyway

The crew brings most value for: ambiguous inputs, hallucination detection, and relative date handling.

## 9. Remaining Issues
- Rule-based tools cannot fix misspelled entity names (case_003 from ЛР12 pattern)
- "ambiguous" always becomes manual_review — an LLM could sometimes resolve it
- FallbackHandler's re-extraction is identical to the Extractor's logic, so if the original extraction is wrong due to a systematic tool limitation, fallback produces the same wrong result
- No confidence threshold: even a 51% confidence result passes the Reviewer
- Relative date check fires on any mention of "next/last" — some false positives possible

## 10. What Would Be Fixed Next
1. Add fuzzy entity matching (rapidfuzz) to handle typos
2. Add LLM-based disambiguation for ambiguous categories
3. Differentiate FallbackHandler from Extractor (different strategy, not just re-running same tools)
4. Add confidence threshold check in Reviewer (e.g., flag if confidence < 0.4)
5. Add unit tests per agent to verify reviewer catches specific hallucinations
