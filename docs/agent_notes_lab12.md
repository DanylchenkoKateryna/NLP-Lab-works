# Agent Notes — Lab 12: Tool-grounded Single Agent

## 1. Use Case
**NLP Research Post Analyzer** — a single agent that receives a 20 Newsgroups
post fragment and produces a structured extraction:
category / persons / organizations / locations / dates.
Builds on the corpus from ЛР10 (NER pipeline) and ЛР11 (LLM extraction).

## 2. Agent Task
Given raw text, the agent must:
1. Extract named entities (persons, orgs, locations, dates)
2. Classify the newsgroup category
3. Validate the composed output for schema correctness
4. Return a structured final answer with tool provenance

## 3. Tools Implemented
| Tool | Type | Purpose |
|------|------|---------|
| `extract_entities(text)` | Extraction | Regex + keyword NER |
| `classify_category(text)` | Classification | Keyword-score classifier |
| `validate_extraction(data)` | Validation | Schema + consistency check |

## 4. When the Agent Calls Each Tool
- **Always**: `extract_entities` → `classify_category`
- **Adaptive**: `validate_extraction` only when `raw_count ≥ 1` OR `len(text) > 60`
  (skip for trivially short texts with no entities — validation adds nothing)
- **Early abort**: if `extract_entities` raises, agent stops and returns error

## 5. Logging
Every tool call is recorded by `ToolCallLogger.call()` with:
timestamp, task_id, tool_name, input, output, success, error, reason.
Saved to `docs/tool_logs_lab12.jsonl` (JSONL format, one entry per line).

## 6. What Tools Improved
- **Accuracy**: agent correctly detected "ambiguous" category (cases 006, 008)
  where baseline hallucinated a single category
- **Completeness**: agent found Vatican as org (case 007) which baseline missed
- **No hallucinations**: agent extracted only entities actually present in text
  (case 003 — noisy text — agent returned empty rather than fabricating names)
- **Structured output**: final answer is always a schema-conformant dict
  with provenance traceable to specific tool calls

## 7. Where Tools Were Redundant or Unhelpful
- **case_002, 004**: text has no entities → extraction + validation both return
  empty results; same as baseline. Tools add logging overhead but no insight.
- **case_005**: `validate_extraction` called on a trivial 1-date result — no
  errors or warnings produced. This is the one clear unnecessary call.
- **case_010**: empty input → `extract_entities` raises ValueError → agent aborts.
  Baseline at least returned an empty response without crashing.

## 8. Errors That Remain
- Keyword matching fails on noisy/misspelled text (case 003)
- No fuzzy matching — "Dawkin$$" and "Dawkins" are not linked
- Agent cannot handle None input (requires str) — minor but fixable
- `validate_extraction` does not check cross-field consistency
  (e.g., sci.electronics + religious figures in entities)

## 9. What to Fix Next
1. Add fuzzy string matching (difflib / rapidfuzz) for entity extraction
2. Move tool-selection logic to an LLM planner for dynamic planning
3. Add a `score_confidence(extraction, classification)` tool that cross-validates
   entity types against predicted category
4. Add cross-field consistency check to validator
5. Cache keyword scores to avoid re-scanning text twice
