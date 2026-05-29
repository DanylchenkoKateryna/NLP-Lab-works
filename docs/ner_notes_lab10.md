# NER Analysis Notes — Lab 10

## Corpus & Task

- **Corpus**: 20 Newsgroups (alt.atheism, sci.electronics, soc.religion.christian)
- **Model**: spaCy `en_core_web_sm` v3.8.0 (baseline)
- **Task**: Named entity recognition + hybrid rule post-processing
- **Gold set**: 25 hand-annotated sentences covering all three newsgroups

---

## 1. Baseline Model Behaviour

### What spaCy Gets Right
- Standard **ORG** names: "Intel", "MIT Media Lab", "Hewlett-Packard", "American Atheists",
  "Cleveland State University"
- **GPE** (geo-political entities): "Poland", "Rome", "Arabia", "Skopje"
- **PERSON** (mainstream proper names): "Richard Dawkins", "David Hume", "Mother Teresa",
  "Jesus Christ", "John Paul II" (partial), "Muhammad"
- Standard **DATE** fragments: "November 1971", "June 1979", "August 26, 1910", "2006"
- **NORP**: "Christian", "Islam" (partially — mislabelled ORG)

### What Baseline Misses
1. **All electronics components** — `en_core_web_sm` has no training data for terms like
   *transistor*, *resistor*, *capacitor*, *diode*, *oscilloscope*, *op-amp*, *zener*, etc.
   (10 missed entities in gold set alone)
2. **Full RFC-2822 Usenet dates** — "Thu, 15 Apr 1993 09:45:12 -0500" is only partially
   tagged; spaCy picks up the year fragment ("1993") but misses the rest
3. **Compound religious names** — "Holy Spirit", "John the Baptist", "Pope John Paul II"
   are split or mis-typed by the statistical model

### Common Error Types (Baseline)
| Error | Count | Example |
|-------|-------|---------|
| Missed ELECTRONICS_COMPONENT | 10 | "resistor", "capacitor", "oscilloscope" |
| Boundary (DATE) | 5 | "1993" instead of "Thu, 15 Apr 1993 09:45:12 -0500" |
| Boundary (ORG) | 5 | "MIT" instead of "MIT Media Lab" |
| Boundary (PERSON) | 3 | "John Paul II" instead of "Pope John Paul II" |
| False positive (misc) | 12 | "first" → ORDINAL, "last year" → DATE |

---

## 2. Hybrid Rules

### Rule 1 — ELECTRONICS_COMPONENT (PhraseMatcher)

**Motivation**: spaCy never labels any electronics vocabulary.  
**Vocabulary** (26 terms): transistor, resistor, capacitor, diode, op-amp, mosfet,
oscilloscope, multimeter, voltmeter, ammeter, breadboard, schematic, waveform, oscillator,
rectifier, regulator, zener, bjt, fet, pcb, …  
**Method**: `spacy.matcher.PhraseMatcher` with `attr="LOWER"` → skips any span already
covered by spaCy (avoids double-tagging).

**Effect on gold set**: 0 → 10 correct ELECTRONICS_COMPONENT entities.

### Rule 2 — RELIGIOUS_FIGURE → PERSON (PhraseMatcher)

**Motivation**: Religious compound names are split by spaCy.
"Holy Spirit" → nothing; "John the Baptist" → ["John"(PERSON), "Baptist"(NORP)];
"Pope John Paul II" → "John Paul II"(PERSON) — boundary miss.  
**Vocabulary** (21 names): Jesus Christ, Jesus, Holy Spirit, Virgin Mary,
John the Baptist, Saint Peter, Mother Teresa, Pope John Paul II, Muhammad, …  
**Method**: Phrase matcher adds/corrects spans; `run_hybrid` uses greedy longest-span
deduplication to remove sub-spans.

**Effect on gold set**: Adds "Holy Spirit", "John the Baptist", "Pope John Paul II" correctly;
removes spurious "Baptist"(NORP) and "John Paul II"(PERSON) sub-spans.

### Rule 3 — USENET_DATE (regex)

**Motivation**: RFC-2822 header dates like "Thu, 15 Apr 1993 09:45:12 -0500" appear in
every newsgroup post header. spaCy only tags the year fragment.  
**Method**: Regex with weekday, day, month, year, time, optional timezone.  
**Key fix**: Overlap check is asymmetric — an existing span that is fully *contained*
within the proposed span (e.g., "1993" ⊂ "Thu, 15 Apr 1993 09:45:12 -0500") is allowed
to be superseded. Only truly wider existing spans block the rule.

**Effect on gold set**: 3 boundary_error DATE → 3 correct DATE.

---

## 3. Evaluation Results

| Metric | Baseline | Hybrid | Δ |
|--------|----------|--------|---|
| Correct | 24 | 40 | +16 |
| Missed | 13 | 2 | -11 |
| Type errors | 1 | 1 | — |
| Boundary errors | 15 | 10 | -5 |
| False positives | 12 | 8 | -4 |
| **Precision** | 0.462 | **0.678** | +0.216 |
| **Recall** | 0.453 | **0.755** | +0.302 |
| **F1** | 0.457 | **0.714** | +0.257 |

### Per-type Hybrid Results

| Label | Correct | Missed | FP |
|-------|---------|--------|----|
| PERSON | 12 | 1 | 0 |
| ELECTRONICS_COMPONENT | 10 | 0 | 1 |
| DATE | 9 | 1 | 2 |
| ORG | 3 | 0 | 1 |
| GPE | 4 | 0 | 0 |
| NORP | 2 | 0 | 0 |

---

## 4. Remaining Error Categories

After hybrid post-processing, the dominant error categories are:

1. **Boundary errors (ORG)** — e.g., "The University of California at Berkeley" vs
   "University of California at Berkeley" (article boundary); "The Council of Nicaea"
   vs "Council of Nicaea". These are article-prefix boundary mismatches.

2. **False positives (WORK_OF_ART)** — "The God Delusion", "the Bible" tagged by spaCy
   as WORK_OF_ART (arguably correct, not in gold).

3. **Missed "God"** — Tagged as PERSON in gold but too generic to add to a phrase list
   without massive false positives.

4. **Missed "Pentecost"** — Tagged as DATE in gold; a domain-specific religious calendar
   date not covered by any pattern.

5. **Boundary errors (DATE)** — "the 7th century" vs "7th century"; 
   "14 Apr" partial match within a Usenet date.

---

## 5. What to Improve Next

- Add article-aware ORG boundary normalization (strip leading "The"/"the")
- Extend USENET_DATE_REGEX or add a fallback for partial date matches already in a full match
- Add a RELIGIOUS_DATE rule for terms like "Pentecost", "Easter", "Ramadan"
- Consider fine-tuning `en_core_web_sm` on a small annotated 20-Newsgroups sample
