# Audit Summary -- Lab 11: LLM Extraction (schema-first)

**Date:** 2026-05-29

## 1. Extraction Case
Task: Structured extraction from 20 Newsgroups post fragments
Corpus: 20 Newsgroups -- alt.atheism / sci.electronics / soc.religion.christian
Schema fields (7): category | persons | organizations | locations | dates | has_question | sentiment

## 2. Evaluation Set
Total texts: 20
sci.electronics: 9 | soc.religion.christian: 6 | alt.atheism: 5

## 3. Raw Valid JSON Rate
14 / 20 = 70.0%
Parse failures: 3/20 (code fence, trailing text, not JSON)
Schema violations: 3/20 (missing field, wrong type, enum violation)

## 4. Post-Repair Valid JSON Rate
19 / 20 = 95.0%
Repair needed: 6/20 | Repair fixed: 5/6 (83.3%) | Permanently invalid: 1/20

## 5. Schema-Valid JSON Rate
19 / 20 = 95.0%

## 6. Most Problematic Fields
has_question: string instead of boolean
category: incorrect enum value
sentiment: field omitted by LLM
dates: religious calendar terms treated as dates

## 7. Error Types
parse_error: 3 | schema_violation: 3 | semantic_error: 10

## 8. Schema-first Pipeline Assessment
Repair loop: +25pp improvement (70 -> 95%). Semantic errors not detectable by schema alone.
