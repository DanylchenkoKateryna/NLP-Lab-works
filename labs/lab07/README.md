# Lab 7 — Linear SVM + char-ngrams + imbalance

**Corpus:** 20 Newsgroups — `alt.atheism` / `sci.electronics` / `soc.religion.christian`  
**Task:** Direction A — Text Classification  
**Builds on:** Lab 6 (same split, same baseline)

---

## 1. Classification subtask

3-class Usenet post classification. Input: post body text (footer stripped). Output: one of 3 newsgroup categories. Same stratified 80/10/10 split as ЛР5/ЛР6 (seed=42).

## 2. Lab6 baseline used for comparison

- **Model:** TF-IDF word(1,2) + Logistic Regression (C=1.0)
- **Input:** `clean_text` (Newsgroup footer removed)
- **Reference metrics:** Test Acc ≈ 0.9435, Test Macro-F1 ≈ 0.9441

## 3. SVM variants tested

| Variant | Features | class_weight |
|---|---|---|
| V1 (reference) | word TF-IDF(1,2) + LogReg | no |
| V2 | word TF-IDF(1,2) + LinearSVC | no |
| V3 | word TF-IDF(1,2) + LinearSVC | balanced |
| V4 | word TF-IDF(1,2) + char_wb TF-IDF(3,5) + LinearSVC | no |
| V5 | word TF-IDF(1,2) + char_wb TF-IDF(3,5) + LinearSVC | balanced |

## 4. Class imbalance

Mild imbalance in train: `alt.atheism` is the majority class (~39% of samples); `sci.electronics` is the minority (~30%). Imbalance ratio ≈ 1.3×. `class_weight="balanced"` was tested but had limited impact at this scale.

## 5. Threshold selection

OvR (one-vs-rest) PR-curve analysis for `alt.atheism` — the most-confused class.  
Threshold tuned **on validation set only**. Best-F1 threshold selected (balanced P/R logic), with recall≥0.85 threshold computed as an alternative for recall-first use cases.

## 6. Best model

**LinearSVC with word(1,2) + char_wb(3,5)** (no class_weight) achieved the best or near-best Val Macro-F1, confirming that char-ngrams add value for this corpus by capturing morphological patterns in religious and technical vocabulary.

## 7. What to do next

- Apply sequence models (fastText, LSTM) for better contextual separation of the religion classes.
- Implement quoted-line filtering before TF-IDF to reduce `quoted_only` errors.
- Explore subject-field features as a complementary signal.
- Try SMOTE or focal loss for class imbalance if the ratio widens with more data.

---

## How to run

```bash
# Local
cd <repo-root>
jupyter nbconvert --to notebook --execute notebooks/lab7_linear_svm_char_ngrams.ipynb
```

Or open `notebooks/lab7_linear_svm_char_ngrams.ipynb` in Google Colab and click **Run all**.

## Key files

| Path | Description |
|---|---|
| `notebooks/lab7_linear_svm_char_ngrams.ipynb` | Full experiment notebook |
| `src/svm_experiments.py` | run_logreg_baseline, run_linear_svc, run_svc_word_char, plot_* |
| `src/threshold_eval.py` | find_best_f1_threshold, threshold_summary |
| `src/classification_baseline.py` | strip_footer, make_pipeline (ЛР6 module, reused) |
| `data/sample/splits_*_ids.txt` | Train/val/test split IDs (unchanged from ЛР5) |
| `docs/class_distribution_lab7.png` | Class balance bar charts |
| `docs/pr_curve_lab7.png` | PR curve for alt.atheism OvR |
| `docs/confusion_matrix_lab7.png` | Side-by-side CM: LogReg vs LinearSVC word+char |
| `tests/error_cases_lab7.jsonl` | Misclassified examples with error categories |
| `docs/audit_summary_lab7.md` | Auto-generated metrics + findings report |
