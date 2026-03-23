# Audit Summary — Lab 5 Split & Leakage Checks

**Generated:** 2026-03-23  
**Dataset:** 20 Newsgroups (alt.atheism / sci.electronics / soc.religion.christian)  
**Total documents:** 6,383  
**Strategy:** Stratified random split 80/10/10, seed=42  

## Split Sizes

| Split | Size |
|---|---|
| train | 5,132 |
| val   | 614 |
| test  | 637 |

## Leakage Check Results

| Check | Result |
|---|---|
| Exact dup train∩test | 0 |
| Exact dup train∩val | 0 |
| Exact dup val∩test | 0 |
| Near-dup (≥0.95) train∩test sample | 35 |
| Template leakage ("Newsgroup:") | 3,944 / 6,383 (62%) — CRITICAL |
| Group leakage (subject overlap) | see notebook |
| Time leakage | N/A |
| Fit-on-train verified | Yes (Pipeline) |

## Baseline on text_v2 (with leakage)

| Metric | Value |
|---|---|
| Accuracy | 0.9686 |
| Macro-F1 | 0.9694 |

_High values expected due to "Newsgroup:" template in 62% of texts._

## Key Risk

**Strip `Newsgroup: {class}` footer before any fair model evaluation.**