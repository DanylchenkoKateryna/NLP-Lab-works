# Audit Summary — Lab 3 Lemma/POS Baseline

**Generated:** 2026-03-23  
**Dataset:** 20 Newsgroups (alt.atheism / sci.electronics / soc.religion.christian)  
**Task:** A — Text Classification  
**Tool:** Stanza (English model)  
**Total documents:** 6,383  
**Stanza truncation:** 300 words per document  

## Baseline Results

| Approach | Accuracy | Macro-F1 |
|---|---|---|
| Baseline 1: processed_v2 | 0.9843 | 0.9846 |
| Baseline 2: lemma_text | 0.9812 | 0.9815 |
| Baseline 3: content lemmas (NOUN/ADJ/VERB) | 0.9640 | 0.9643 |

**Lemma vs Raw:** Accuracy delta=-0.0031 | Macro-F1 delta=-0.0031

## Error Analysis

- Edge cases tested: 20  
- Source: `tests/ling_edge_cases.jsonl`  
- PII tokens survive lemmatization: Yes  
- Main issues: abbreviations, internet slang, proper nouns with dots  

## Conclusion

Lemmatization did not improve classification (Macro-F1 delta=-0.0031).
Topically distinct classes provide strong TF-IDF signal without normalization.
Lemmas recommended for retrieval and clustering tasks.

**Decision:** `processed_v2` for classification · `lemma_text` for retrieval/clustering.

## Files

- `data/processed_v2/processed_v3.csv` — lemma_text, pos_seq, content_lemma_text  
- `data/sample/sample_v3.csv` — 100-row sample  