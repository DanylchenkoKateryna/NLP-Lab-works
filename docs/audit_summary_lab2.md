# Audit Summary — Lab 2 Cleaning & Normalization

**Generated:** 2026-03-23  
**Pipeline version:** v2  
**Total documents:** 6,383  

## Before vs. After

| Metric | Before (raw) | After (v2) | Change |
|---|---|---|---|
| Empty texts | 0 | 7 | — |
| Very short (<5 words) | 10 | 28 | — |
| Exact duplicates | 17 | 1044 | — |
| Mean char length | 1,844.2 | 1,263.5 | 31% drop |
| Median char length | 1,183 | 700 | — |
| Mean word count | 299.7 | 216.5 | 28% drop |
| Median word count | 185 | 117 | — |
| Mean sentence count | N/A | 13.2 | new metric |

## PII Replacements

- URLs masked    : **2**
- Emails masked  : **13,879**
- Phones masked  : **1,215**
- Quote lines removed: **48,397**

## Regression Tests

- Idempotence          : `PASS`
- No empty explosion   : `PASS`
- Empty input safety   : `PASS`

## Edge Cases

- Total edge cases tested: **30**
- Source: `tests/edge_cases.jsonl`

## Files Generated

- `data/processed_v2/processed_v2.csv` — full preprocessed dataset
- `data/sample/sample_raw.csv` — 100-row raw sample
- `data/sample/sample_processed_v2.csv` — 100-row processed sample