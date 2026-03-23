# Lab 6 — TF-IDF + Logistic Regression Baseline

**Corpus:** 20 Newsgroups — `alt.atheism` / `sci.electronics` / `soc.religion.christian`
**Task:** A — Text Classification
**Method:** TF-IDF vectorization + Logistic Regression (sklearn Pipeline)

---

## 1. Direction and Task

**Direction A — Text Classification.**
3-class classification of Usenet newsgroup posts into:
`alt.atheism` / `sci.electronics` / `soc.religion.christian`.
Input: raw or pre-cleaned post text. Output: one of 3 class labels.

---

## 2. Two Baselines Compared

| Baseline | Feature extraction | Input text | Notes |
|---|---|---|---|
| **B1 (leaky)** | TF-IDF word unigrams (1,1), max 20k features, sublinear TF | `text_v2` (raw, footer intact) | Contains `Newsgroup: {class}` in 62% of docs — direct label leak |
| **B2 (honest)** | TF-IDF word 1-2 grams (1,2), max 20k features, sublinear TF | `clean_text` (footer stripped via regex) | Realistic evaluation; bigrams add phrase-level signal |

Both use `LogisticRegression(C=1.0, solver='lbfgs', max_iter=500, seed=42)`.
Split: stratified 80/10/10, seed=42 from ЛР5 (`data/sample/splits_*_ids.txt`).

---

## 3. Key Metrics

| Baseline | Val Acc | Val F1 | Test Acc | Test F1 |
|---|---|---|---|---|
| B1 (leaky, raw) | 0.9805 | 0.9808 | 0.9733 | 0.9740 |
| B2 (honest, clean) | 0.9658 | 0.9662 | 0.9435 | 0.9441 |

Removing the `Newsgroup:` footer leak drops accuracy by **3.0 pp** (0.9733 → 0.9435) — confirming the template leakage finding from ЛР5.
The classes are still well-separable by content alone (94.4% is a strong honest baseline).

---

## 4. Error Analysis Findings

- **class_overlap (religion)** — largest error source: `alt.atheism` and `soc.religion.christian` share heavy overlapping theological vocabulary; TF-IDF unigrams/bigrams cannot distinguish them reliably.
- **short_text** — posts with fewer than ~200 characters provide insufficient TF-IDF signal; the model defaults to the majority class.
- **quoted_only** — posts that consist mostly of cited lines (`>`) carry the original author's topic rather than the reply's intent.
- `sci.electronics` is the easiest class to classify (unique technical terminology).

Full error table: `tests/error_cases_lab6.jsonl`.

---

## 5. What to Fix Next

- Add character 3-6 grams or subword features to improve religion-class separation.
- Apply a length-aware fallback (prior distribution) for very short posts.
- Pre-filter quoted lines (`>` prefix) before TF-IDF (already in `clean_text` from Lab 2).
- Try a subject-aware or thread-aware data split for a realistic generalisation estimate.
- Compare against a LinearSVC baseline and a Naive Bayes prior.

---

## How to Run

```bash
# Local
cd <repo-root>
python -m jupyter nbconvert --to notebook --execute notebooks/lab6_tfidf_logistic_baseline.ipynb
```

Or open `notebooks/lab6_tfidf_logistic_baseline.ipynb` in Google Colab and click **Run all**.

## Key Files

| Path | Description |
|---|---|
| `src/classification_baseline.py` | Core module: `strip_footer`, `make_pipeline`, `evaluate`, `top_features_per_class` |
| `notebooks/lab6_tfidf_logistic_baseline.ipynb` | Full experiment notebook |
| `data/sample/splits_*_ids.txt` | Train/val/test split IDs from ЛР5 |
| `data/processed_v2/processed_v2.csv` | Source dataset (text_v2, label_id, category) |
| `docs/confusion_matrix_lab6.png` | Side-by-side confusion matrices (B1 vs B2) |
| `tests/error_cases_lab6.jsonl` | B2 misclassified examples with error categories |
| `docs/audit_summary_lab6.md` | Auto-generated metrics + findings report |
