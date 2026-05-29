# Lab 10 — NER Pipeline + Hybrid Rules

## Objective

Build a Named Entity Recognition (NER) pipeline for the 20 Newsgroups corpus
using spaCy's `en_core_web_sm` as the statistical baseline, then extend it with
three targeted hybrid rules to cover domain-specific entity types the baseline misses.
Evaluate using a 25-sentence hand-annotated gold set (rough precision / recall / F1).

---

## Corpus

| Property | Value |
|----------|-------|
| Source | 20 Newsgroups (sklearn) |
| Categories | alt.atheism · sci.electronics · soc.religion.christian |
| Documents | 6,376 |
| Text field | `text_v2` (PII-masked, Unicode-normalised) |

---

## Files

| File | Description |
|------|-------------|
| `notebooks/lab10_ner_pipeline_hybrid_rules.ipynb` | Main notebook — Colab-ready, pre-executed |
| `src/ner_pipeline.py` | spaCy model loader + inference utilities |
| `src/ner_rules.py` | Three hybrid rules + `HybridNERPipeline` class |
| `src/ner_eval.py` | 25-sentence gold set, evaluation metrics, error analysis |
| `docs/ner_notes_lab10.md` | Manual analysis notes |
| `docs/audit_summary_lab10.md` | Auto-generated audit summary |

---

## Baseline Model

- **Model**: `en_core_web_sm` v3.8.0
- **Standard labels**: CARDINAL, DATE, EVENT, GPE, LANGUAGE, LAW, LOC,
  MONEY, NORP, ORDINAL, ORG, PERCENT, PERSON, PRODUCT, QUANTITY, TIME, WORK_OF_ART
- **Baseline P/R/F1 on gold set**: 0.462 / 0.453 / 0.457

### Key Baseline Failures

1. **All electronics components** — `en_core_web_sm` has no electronics training data.
   Terms like *transistor*, *resistor*, *capacitor*, *oscilloscope* are entirely missed
   (10 of 11 gold ELECTRONICS_COMPONENT entities missed).
2. **Usenet RFC-2822 dates** — "Thu, 15 Apr 1993 09:45:12 -0500" is only partially
   tagged (year fragment "1993"), missing the full date string.
3. **Compound religious names** — "Holy Spirit" → nothing; "John the Baptist" → split
   into "John"(PERSON) + "Baptist"(NORP); "Pope John Paul II" → "John Paul II" (boundary).

---

## Hybrid Rules

### Rule 1 — ELECTRONICS_COMPONENT

**Method**: `spacy.matcher.PhraseMatcher` with `attr="LOWER"` on a 26-term vocabulary.  
**Vocabulary**: transistor, resistors, capacitor, diode, op-amp, mosfet, oscilloscope,
multimeter, voltmeter, breadboard, schematic, waveform, oscillator, rectifier,
regulator, zener, bjt, fet, pcb, …  
**Effect**: 0 → 10 correct ELECTRONICS_COMPONENT entities.

### Rule 2 — RELIGIOUS_FIGURE → PERSON

**Method**: `PhraseMatcher` on 22 compound religious names + greedy longest-span
deduplication (removes sub-span false positives introduced by the phrase matcher
overlapping with shorter spaCy spans).  
**Names**: Jesus Christ, Holy Spirit, Virgin Mary, John the Baptist,
Pope John Paul II, Mother Teresa, Saint Peter, Muhammad, …  
**Effect**: PERSON 9 → 12 correct; boundary errors 3 → 1.

### Rule 3 — USENET_DATE

**Method**: Regex matching RFC-2822 date format with weekday prefix and optional
timezone offset. Key feature: asymmetric overlap check — an existing spaCy span
fully contained within the proposed match (e.g. "1993" ⊂ "Thu, 15 Apr 1993 …") is
superseded rather than blocking the rule.  
**Regex**: `(?:Mon|Tue|...|Sun), \d{1,2} (?:Jan|...) \d{4} \d{2}:\d{2}(:\d{2})? (?:[+-]\d{4}|[A-Z]{2,4})?`  
**Effect**: DATE 6 → 9 correct (+3 Usenet dates fully recovered).

---

## Evaluation Results

| Metric | Baseline | Hybrid | Delta |
|--------|----------|--------|-------|
| Correct | 24 | 40 | +16 |
| Missed | 13 | 2 | −11 |
| Type errors | 1 | 1 | — |
| Boundary errors | 15 | 10 | −5 |
| False positives | 12 | 8 | −4 |
| **Precision** | 0.462 | **0.678** | +0.216 |
| **Recall** | 0.453 | **0.755** | +0.302 |
| **F1** | 0.457 | **0.714** | +0.257 |

---

## Error Analysis (Hybrid)

| Category | Count | Root Cause |
|----------|-------|------------|
| `boundary_error` | 10 | Article prefix ("The Council" vs "Council"); partial number overlaps |
| `false_positive` | 8 | spaCy noise: ORDINAL "first", CARDINAL/DATE on measurements |
| `missed` | 2 | "God" (too generic), "Pentecost" (religious calendar date) |
| `type_error` | 1 | "Islam" → ORG instead of NORP |

---

## What to Improve Next

- Strip leading article from ORG spans ("The Council" → "Council")
- RELIGIOUS_DATE rule: Pentecost, Easter, Ramadan, Passover
- Add "Islam" to NORP phrase list (fix type_error)
- Whitelist filter for common spaCy FPs (ORDINAL "first", DATE on measurement strings)
- Fine-tune `en_core_web_sm` NER head on a small annotated 20-Newsgroups sample

---

## How to Run

### Google Colab

Open the notebook badge at the top of `lab10_ner_pipeline_hybrid_rules.ipynb`.
Cell 2 installs spaCy and downloads `en_core_web_sm` automatically.

### Local

```bash
pip install spacy>=3.7.0
python -m spacy download en_core_web_sm
jupyter notebook notebooks/lab10_ner_pipeline_hybrid_rules.ipynb
```
