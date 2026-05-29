# Audit Summary — Lab 12: Tool-grounded Single Agent

**Date:** 2026-05-29

## 1. Use Case
NLP Research Post Analyzer — structured extraction from 20 Newsgroups posts.
Builds on corpus from ЛР10 (NER) and ЛР11 (LLM extraction schema-first).

## 2. Tools Implemented
- extract_entities(text)     — regex + keyword NER (PERSON, ORG, GPE, DATE)
- classify_category(text)    — keyword-score newsgroup classifier (3 categories)
- validate_extraction(data)  — schema + consistency validator

## 3. Test Cases
10 cases covering: simple, missing_data, noisy_text, empty_result,
unnecessary_tool, ambiguous, two_tools_sequential, validator_finds_problem,
answer_relies_on_tool, tool_fails.

## 4. Tool Call Success Rate
27 / 28 = 96.4%
Failed: 1 (case_010 extract_entities raised ValueError for empty input)

## 5. Average Tool Calls per Task
2.8 (28 calls / 10 tasks)

## 6. Tasks That Benefited from Tools
5 / 10 = 50%
Best cases: ambiguity detection (006, 008), complete entity extraction (007),
no-hallucination extraction (001, 009).

## 7. Unnecessary Tool Calls
1 — case_005: validate_extraction called on trivial 1-date result with no issues.

## 8. Best Tool Use Examples
- case_007: agent found Vatican as org (missed by baseline) + 6 total entities
- case_006: agent correctly returned "ambiguous" vs baseline's wrong single category
- case_008: validator caught ambiguous category as blocking error; baseline missed entirely

## 9. Problematic Examples
- case_003: noisy text with misspellings — keyword tools returned empty; baseline hallucinated
- case_010: empty input — tool raised, agent aborted (graceful but unhelpful)
- case_005: unnecessary validate call; trivial text needed only 2 tools

## 10. What to Improve Next
1. Fuzzy entity matching (rapidfuzz) for noisy/misspelled text
2. Dynamic tool selection via LLM planner instead of rule-based policy
3. Cross-field consistency check in validator (entity types vs category)
4. Pre-flight guard: reject empty/null inputs before calling any tool
5. Disambiguation tool for ambiguous category cases
