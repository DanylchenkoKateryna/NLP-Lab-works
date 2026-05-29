# Lab 9 — Word Embeddings: Word2Vec / FastText

## 1. Corpus

20 Newsgroups — 3 categories: `alt.atheism` (2,396), `sci.electronics` (1,967), `soc.religion.christian` (2,013).  
Total: 6,376 documents, ~1.3M tokens. Text field: `text_v2` (Lab 2 PII-masked).

## 2. Models Trained

| Model | Algorithm | Vocab |
|-------|-----------|-------|
| Word2Vec | Skip-Gram | 18,613 |
| FastText | Skip-Gram + subwords (min_n=3, max_n=6) | 18,613 |

## 3. Hyperparameters

```
vector_size = 100
window      = 5
min_count   = 3
sg          = 1   # Skip-Gram
epochs      = 10
seed        = 42
```

Both models use identical base parameters for fair comparison.

## 4. Word Types Analysed

| Type | Example words |
|------|--------------|
| frequent | god, church, believe |
| domain (electronics) | voltage, circuit, resistor, ground |
| domain (religion) | church, resurrection, omnipotent |
| noisy / metadata | atheism, electronics |
| morph-variant | scripture, sin, circuit |
| rare | omnipotent, scripture |

## 5. Five Most Interesting Cases

| # | Word | Verdict | Key finding |
|---|------|---------|-------------|
| 1 | `voltage` | ✅ Useful | Both models: clean electronics cluster (divider/regulator/transistor) |
| 2 | `church` | ✅ Useful | Both models: religious institution cluster (catholic/coptic/communion) |
| 3 | `believe` | ❌ Weak | W2V: random typos (sufficent, partents, lilac) — no semantic signal |
| 4 | `atheism` | ❌ Weak | W2V top neighbor = `alt` (0.86) from "alt.atheism" header |
| 5 | `scripture` | ⚠️ Mixed | W2V: noise; FT: scriptures/scriptural/scriptura via subwords |

## 6. FastText Better / Worse

**FastText better:**
- Morphologically rich words: scripture, circuit, omnipotent, believe, atheism
- Rare words with few co-occurrence contexts

**FastText not clearly better:**
- Frequent, well-represented words: voltage, church, ground, resistor
- `jesus`: W2V gives christ/luke/matthew (semantic); FT gives jesu/jeesus (morphological noise)

## 7. Are Embeddings Useful for This Corpus?

**Partially.** Domain-specific clusters work well (electronics: voltage/circuit/resistor; religion: church/catholic). Generic discourse words (believe, think, know) produce noisy neighborhoods. Metadata contamination from newsgroup headers (alt.atheism, sci.electronics) contaminates some terms.

**Recommended use:** corpus vocabulary exploration and domain term expansion — not as primary classification features (TF-IDF SVM from Lab 7 remains the stronger classifier for this corpus).

## 8. Files

| File | Description |
|------|-------------|
| `notebooks/lab9_word_embeddings_fasttext_word2vec.ipynb` | Main notebook |
| `src/embeddings_train.py` | Training utilities (tokenize, train_word2vec, train_fasttext) |
| `src/embeddings_eval.py` | Evaluation utilities (neighbors, comparison table, audit generator) |
| `docs/embedding_notes_lab9.md` | Manual analysis notes |
| `docs/audit_summary_lab9.md` | Auto-generated audit summary |
