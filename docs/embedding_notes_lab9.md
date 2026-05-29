# Embedding Notes — Lab 9: Word2Vec / FastText

**Date:** 2026-05-29

---

## 1. Corpus

- **Dataset:** 20 Newsgroups — 3 categories
  - `alt.atheism`: 2,396 documents
  - `sci.electronics`: 1,967 documents
  - `soc.religion.christian`: 2,013 documents
- **Total after filtering empty:** 6,376 documents
- **Total tokens:** ~1,297,472
- **Vocab size (gensim, min_count=3):** 18,613
- **Text field:** `text_v2` (Lab 2 PII-masked, Unicode-normalised)
- **Tokenization:** word-level regex `[a-z][a-z'-]{1,}`, lowercase, no lemmatisation

---

## 2. Models

| Model | Algorithm | Params |
|-------|-----------|--------|
| Word2Vec | Skip-Gram | vector_size=100, window=5, min_count=3, epochs=10, seed=42 |
| FastText | Skip-Gram + subwords | same base + min_n=3, max_n=6 |

**Why Skip-Gram?** Better than CBOW for rare and domain-specific words (electronics components, theological vocabulary), which are important for this corpus.

---

## 3. 10 Words for Nearest Neighbors

| Word | Type | W2V top-5 | FT top-5 |
|------|------|-----------|----------|
| `god` | frequent | all-knowing, spinoza's, necessay, plausibility | god-, god--, gods', god's, lovingkindness |
| `church` | frequent+domain | catholic, churches, coptic, cornerstone, bride | churchs, church's, churches, catholic, catholique |
| `voltage` | domain | divider, rectified, regulator, volts, gradient | voltatge, voltages, overvoltage, volt, volts |
| `circuit` | domain | cue, impedance, bipolar, feedback, imbalance | circuitry, circuits, circa, diagram, op-amps |
| `atheism` | noisy | alt, moderated, insinuated, unum, benedikt | atheism's, autotheism, monotheism, pantheism, theism |
| `scripture` | morph-variant | exlcude, genuine, fulfiller, hebrews, admonitions | scripture', scriptura, scriptures, scriptural, genuine |
| `believe` | noisy | not-, sufficent, partents, nothingness, lilac | believeit, believeing, believeth, disbelieve, believer |
| `resistor` | rare+domain | probe, zener, ohm, bipolar, collector | photoresistor, resistors, phototransistor, transistor, transient |
| `sin` | morph-variant | hates, sinner, forgivenss, tainted, infected | sins, sinlessness, sinner, sinful, sinai |
| `ground` | domain | neutral, conductor, interrupter, wire, breaker | ground', grounded, grounds, grounding, underground |

---

## 4. 5 Domain Terms

### `voltage` (electronics)
- **Word2Vec:** divider(0.76), rectified(0.74), regulator(0.73), volts(0.73), transistor(0.72)
- **FastText:** voltatge(0.94), voltages(0.92), overvoltage(0.88), volt(0.87), volts(0.83)
- **Assessment:** USEFUL both. W2V gives semantic electronics context; FT adds morphological forms. Best case.

### `transistor` (electronics)
- **Word2Vec:** regulated(0.83), gnd(0.77), zener(0.77), strobe(0.76), vdd(0.76)
- **FastText:** phototransistor(0.96), transistors(0.93), photoresistor(0.88), resistor(0.85)
- **Assessment:** USEFUL both. W2V: circuit-level context. FT: component family via subwords.

### `resurrection` (religion)
- **Word2Vec:** resurrected(0.75), christ's(0.69), crucifixion(0.68)
- **FastText:** post-resurrection(0.91), resurection(0.87), resurrected(0.84)
- **Assessment:** PARTLY. W2V: semantic (crucifixion). FT: morphological variants including typos.

### `omnipotent` (religion)
- **Word2Vec:** omnipresent(0.72), accredit(0.61), justifiably(0.61)
- **FastText:** omnipotens(0.94), omnipotence(0.91), omnipresent(0.89), omnipresence(0.87), omniscience(0.84)
- **Assessment:** FT >> W2V. FT builds full attribute cluster (omnipotence/omniscience) via subword n-grams.

### `atheism` (atheism discourse)
- **Word2Vec:** alt(0.86), moderated(0.62), insinuated(0.61) — **newsgroup header contamination**
- **FastText:** atheism's(0.92), autotheism(0.88), monotheism(0.82), pantheism(0.82), theism(0.78)
- **Assessment:** W2V WEAK. Top neighbor `alt` comes from "alt.atheism" in text_v2 metadata. FT better.

---

## 5. Five Cases "Useful / Not Useful"

### Case 1: `voltage` — ✅ USEFUL
- **W2V:** divider, rectified, regulator, volts, transistor
- **FT:** voltages, overvoltage, voltmeter
- **Why useful:** Clean electronics domain cluster in both models. Practical value for query expansion.

### Case 2: `church` — ✅ USEFUL
- **W2V:** catholic, churches, coptic, communion, pentecostal
- **FT:** church's, churches, catholic, coptic, apostolic
- **Why useful:** Pure religious institution cluster. No cross-domain confusion. High domain alignment.

### Case 3: `believe` — ❌ NOT USEFUL
- **W2V:** not-, sufficent, partents, nothingness, lilac
- **FT:** believeit, believeing, believer (morphological only)
- **Why weak:** W2V gives random typos that co-occur in Usenet arguments. `believe` is a generic discourse word used across all 3 categories — no domain specificity.

### Case 4: `atheism` — ❌ NOT USEFUL (W2V)
- **W2V:** alt(0.86) — newsgroup label artifact. Other: FAQ header tokens.
- **FT:** monotheism, pantheism, theism — better, but `alt` still ranks 3rd.
- **Why weak:** `text_v2` retains "Newsgroup: alt.atheism" footer, so `atheism` and `alt` always co-occur. Metadata contamination that preprocessing didn't fully clean.

### Case 5: `scripture` — ⚠️ MIXED
- **W2V:** exlcude, genuine, fulfiller, hebrews (mostly noise)
- **FT:** scriptura, scriptures, scriptural, epistles (excellent)
- **Why mixed:** W2V fails — word too rare for stable neighborhood. FastText recovers via subword n-grams (scrip-, -ture, -tures, -tural). Clear FastText advantage.

---

## 6. Word2Vec vs FastText Comparison

### Where both were similar
- `voltage`, `church`, `ground`, `resistor` — frequent domain words with enough training signal for both

### Where FastText was better
- `scripture` — scriptures/scriptural/scriptura via subwords
- `circuit` — circuitry/circuits cleaner than W2V
- `believe` — morphological forms vs random typos in W2V
- `atheism` — theism/monotheism vs newsgroup label artifact
- `omnipotent` — omnipotence/omniscience cluster via subwords

### Where Word2Vec was competitive
- `jesus` — W2V: christ/luke/matthew/incarnate (semantic); FT: jesu/jeesus (morphological noise)
- `sin` — W2V: sinner/tainted/infected (semantic context); FT: morphological forms only
- `voltage` — W2V gives richer semantic circuit context

---

## 7. Overall Conclusion

**FastText is the better model for this corpus.**

1. Usenet text has high morphological variability and spelling noise → FastText wins via subwords
2. Corpus (~1.3M tokens) is borderline for Word2Vec on rare words
3. W2V still competitive on frequent, well-represented domain words
4. Metadata noise (newsgroup headers) affects both models equally
5. Embeddings give genuine signal for domain-specific vocabulary (electronics, religion)
   but fail on generic discourse words (believe, think, know) — consistent with Lab 8 findings
