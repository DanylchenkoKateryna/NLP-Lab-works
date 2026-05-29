# Audit Summary — Lab 9: Word Embeddings (Word2Vec / FastText)

**Date:** 2026-05-29


## 1. Corpus
- Documents  : **6376**
- Total tokens: 1,297,472
- Vocab size  : 18,613
- Text field  : `text_v2`
- Categories  : alt.atheism (2,396), sci.electronics (1,967), soc.religion.christian (2,013)

## 2. Models Trained
- Word2Vec — Skip-Gram, vector_size=100, window=5, min_count=3, epochs=10
- FastText  — Skip-Gram + subwords (min_n=3, max_n=6), same base params

## 3. Hyperparameters
```
vector_size = 100
window = 5
min_count = 3
sg = 1 (Skip-Gram)
epochs = 10
seed = 42
fasttext_min_n = 3
fasttext_max_n = 6
```

## 4. Strongest Nearest-Neighbor Examples (2–3)
- **voltage** (domain): divider, rectified, regulator, volts, transistor
  > Perfect electronics cluster. Practical value: query expansion.
- **church** (frequent): catholic, churches, coptic, communion, pentecostal
  > Pure religious institution cluster. No cross-domain confusion.
- **omnipotent** (rare): FT: omnipotence, omnipresent, omnipresence, omniscience
  > FastText: full theological attribute cluster via subwords.

## 5. Weakest Examples (2–3)
- **believe** (frequent+noisy): not-, sufficent, partents, nothingness, lilac
  > Problem: W2V: random typos. Too generic for this corpus size.
- **atheism** (noisy): alt(0.86), moderated, insinuated
  > Problem: Newsgroup header contamination — 'alt' is W2V #1 neighbor from 'alt.atheism' label.

## 6. Domain Terms That Were Meaningful
- voltage — clean electronics cluster (both models)
- transistor — circuit-level W2V; component family FT
- resurrection — crucifixion/resurrected W2V; morphological FT
- omnipotent — FT excellent (omnipotence/omniscience cluster)

## 7. Where FastText Won
Morphologically rich words: scripture (scriptures/scriptural), circuit (circuitry), believe (believer/believeth), atheism (monotheism/pantheism), omnipotent (omnipotence).
Rare words where W2V lacks training signal — FastText recovers via subword n-grams.

## 8. Where There Was No Clear Winner
Frequent well-represented words: voltage, church, ground, resistor.
W2V richer semantically for 'jesus' (christ/luke/matthew) vs FT morphological (jesu/jeesus).

## 9. Overall Conclusion
FastText is the better model for this corpus.
Usenet text has high morphological variability and spelling noise;
FastText handles this via subwords. Corpus size (1.3M tokens) is borderline —
Word2Vec works for frequent domain words but fails on rare ones.

## 10. Worth Using Embeddings Further?
Partially. Embeddings give genuine signal for electronics domain (voltage/circuit/resistor)
and religion (church/catholic/coptic).
Not useful for generic discourse words (believe, think) or metadata-contaminated tokens.
Recommended use: corpus vocabulary exploration and domain term expansion,
not as primary classification features.
