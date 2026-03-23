# Leakage Risk Report — Lab 5: Split & Leakage Checks

**Dataset:** 20 Newsgroups — `alt.atheism` / `sci.electronics` / `soc.religion.christian`
**Total documents:** 6,383 (after ЛР2 preprocessing)
**Generated:** see `docs/splits_manifest_lab5.json`

---

## 1. Split Strategy

**Strategy chosen: Stratified random split (80 / 10 / 10)**

The corpus consists of 6,383 independent newsgroup posts across three categories. There is no temporal ordering that must be respected (newsgroup posts do not exhibit measurable concept drift within the collected period), and there are no explicit user or thread IDs that would require group-level splitting. The mild class imbalance (alt.atheism 38%, soc.religion.christian 31%, sci.electronics 31%) is preserved exactly in every split via stratification on `label_id`. A deterministic seed (42) guarantees that the same command always produces the same partition. The 80/10/10 ratio gives 5,106 train / 638 val / 639 test examples, each split having ≥ 190 examples per class — well above the 10–20 minimum required for reliable metric estimation.

---

## 2. Split Statistics

| Split | Size | alt.atheism | sci.electronics | soc.religion.christian |
|---|---|---|---|---|
| train | 5,106 | ~38% | ~31% | ~31% |
| val | 638 | ~38% | ~31% | ~31% |
| test | 639 | ~38% | ~31% | ~31% |

*(Exact numbers generated in `docs/splits_manifest_lab5.json`)*

---

## 3. Leakage Check Results

| Check | Result | Severity |
|---|---|---|
| Exact duplicate train∩test | 0 | ✓ clean |
| Exact duplicate train∩val | 0 | ✓ clean |
| Exact duplicate val∩test | 0 | ✓ clean |
| Near-duplicate (cosine ≥ 0.95) train∩test | see notebook | low |
| **Template leakage: "Newsgroup: {class}"** | **3,944 / 6,383 docs (62%)** | **⚠ CRITICAL** |
| Group leakage (author/thread) | not checked — no group ID column | medium risk |
| Time leakage | N/A — no date column | N/A |
| Fit-on-train-only (TF-IDF) | verified via Pipeline | ✓ clean |

---

## 4. Critical Finding — Template Leakage

**3,944 documents (62%) contain the string `"Newsgroup: <category_name>"` at the end of the text** (appended during ЛР1 data collection). This is a direct label-in-text leak: any model that reads the full `text_v2` column can trivially achieve near-100% accuracy without understanding language. Additionally, `document_id:` metadata appears in 3,938 texts.

**Impact:** All classification metrics computed on `text_v2` as-is are **artificially inflated** and do not reflect real linguistic generalisation.

**Mitigation:** Strip the trailing metadata block (`Newsgroup: …\ndocument_id: …`) before any model training. Use `src/preprocess.py` extended rules or a targeted regex. Until cleaned, treat all accuracy figures as upper-bound estimates, not true performance.

---

## 5. Remaining Risks

- **Template leakage** is the dominant risk; metrics on raw `text_v2` cannot be trusted without the fix described above.
- **Author/thread group leakage:** the same person may have written posts in both train and test (subjects are partially shared). Without author-level splits, the model may benefit from writing-style memorisation rather than topic understanding.
- **Near-duplicates:** a small number of very similar posts (forwarded content, cross-posts) may appear in both train and test despite different IDs.
- **Class imbalance (mild):** alt.atheism is ~7% larger than the other two classes; stratification controls this at split time, but the imbalance still affects model calibration.

---

## 6. Next Steps

- Extend `preprocess.py` to strip the `Newsgroup:`/`document_id:` metadata footer before training.
- Re-run ЛР3 baselines on cleaned text to get honest Macro-F1.
- Consider author-based group split in future labs to assess generalisation across writers.
