# Audit Summary — Lab 4 Rule-Based IE

**Generated:** 2026-03-23  
**Dataset:** 20 Newsgroups (alt.atheism / sci.electronics / soc.religion.christian)  
**Task:** A — Text Classification  
**Method:** Regex + dictionaries (no LLM)  

## Field Types

| Field Type | Definition summary |
|---|---|
| DATE | Calendar dates with month names or ISO format |
| ELEC_QTY | Electrical/physical quantities (V, A, Hz, Ohm, W, F, H, dB) |
| SCRIPTURE_REF | Bible/Quran verse references (Book Chapter:Verse) |

## Precision Results

| Field Type | TP | FP | Total | Precision |
|---|---|---|---|---|
| DATE | 39 | 0 | 39 | 1.000 |
| ELEC_QTY | 77 | 0 | 77 | 1.000 |
| SCRIPTURE_REF | 164 | 0 | 164 | 1.000 |

## Edge Case Tests

**Total cases:** 30  
**Pass rate:** 100.0%  

## Anti-Rules Applied

- Reject ELEC_QTY if preceded by alpha char (part numbers)
- Require colon/dot separator for ambiguous single-word book names
- DATE requires month token or ISO format (no bare 4-digit years)
- ELEC_QTY pattern requires leading digit (rejects `.1uF`)

## Files

- `src/ie_rules.py` — extractor module (regex + dicts)
- `data/sample/lab4_gold_ie.jsonl` — gold subset (120 entries, 64 texts)
- `tests/ie_edge_cases.jsonl` — 30 edge cases
- `docs/ie_policy.md` — field-type specification
- `resources/` — months_en.json, elec_units.json, bible_books.json