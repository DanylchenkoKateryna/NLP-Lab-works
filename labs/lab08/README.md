# Lab 8 — Topic Modeling: LSA / LDA

## 1. Corpus

**20 Newsgroups** — 3-class subset (English, Usenet posts, 1990s)

| Class | Documents |
|-------|-----------|
| `alt.atheism` | ~2,405 |
| `sci.electronics` | ~1,975 |
| `soc.religion.christian` | ~2,003 |
| **Total (after filtering)** | **~6,350** |

**Input data:** `data/processed_v2/processed_v2.csv` (cleaned, PII-masked, newsgroup footer stripped)

## 2. Models Trained

| Model | Vectorizer | Decomposition |
|-------|-----------|--------------|
| LSA | TF-IDF (`sublinear_tf=True`) | `TruncatedSVD` |
| LDA | `CountVectorizer` | `LatentDirichletAllocation` |

**Shared vectorizer params:** `analyzer='word'`, `ngram_range=(1,1)`, `min_df=5`, `max_df=0.90`, `stop_words='english'`

## 3. k Values Tested

- **k = 5** (primary analysis)
- **k = 8** (for comparison)

## 4. Best Topics

| Model | Topic | Name | Why it's good |
|-------|-------|------|---------------|
| LDA k=5 | T0 | Electronics Hardware | Circuit/voltage/resistor vocabulary; top docs are exclusively sci.electronics |
| LDA k=5 | T1 | Christian Theology | Jesus/church/bible; top docs are devotional soc.religion.christian posts |
| LDA k=5 | T2 | Atheism Debate | Atheist/evidence/argument; top docs are alt.atheism debate posts |
| LSA k=5 | C1 | Electronics–Religion Axis | Captures the largest vocabulary contrast in the corpus |

## 5. Worst Topics

| Model | Topic | Type | Root cause |
|-------|-------|------|-----------|
| LDA k=5 | T4 | Generic discourse | Usenet conversational style shared across all classes; not captured by standard English stop-words |
| LSA k=5 | C0 | Mixed religion | First SVD component absorbs global variance; merges alt.atheism + soc.religion.christian onto one axis |
| LDA k=8 | T5–T7 | Redundant sub-topics | k=8 too large for a 3-class corpus; splits existing topics instead of finding new ones |

## 6. LSA vs LDA Comparison

**LDA k=5** outperforms LSA k=5 for this corpus:

- LDA produces **3 interpretable topics** that align with the 3 ground-truth classes
- LSA Component 0 conflates `alt.atheism` and `soc.religion.christian` (shared theological vocabulary, different stance)
- LDA topics are probability distributions → top words clearly "belong" to the topic
- LSA components are orthogonal variance axes → harder to read as standalone themes
- Both models produce 1–2 noise/generic topics regardless of k

## 7. Is Topic Modeling Useful for This Corpus?

**Partially yes.** Electronics is clearly separated. The two religious classes (`alt.atheism`, `soc.religion.christian`) share too much vocabulary for clean topic separation — this is the same failure mode observed in classification (Labs 6–7).

Topic modeling is useful for:
- Unsupervised corpus exploration
- Confirming that vocabulary structure reflects class structure
- Identifying generic/noisy vocabulary to improve preprocessing

Topic modeling is **not** a substitute for classification here — the stance difference (pro/contra religion) is invisible to bag-of-words methods.

## Files

| File | Description |
|------|-------------|
| `notebooks/lab8_topic_modeling_lsa_lda.ipynb` | Main notebook (Run All to reproduce) |
| `src/topic_modeling.py` | LSA/LDA model builders, top-words/top-docs extraction |
| `src/topic_utils.py` | Corpus filtering, quality heuristics, audit summary generator |
| `docs/audit_summary_lab8.md` | Auto-generated audit summary |
| `docs/topic_notes_lab8.md` | Manual topic interpretation notes |
