# Preprocessing Policy — 20 Newsgroups (Lab 2)

**Dataset:** 20 Newsgroups Classification (alt.atheism / sci.electronics / soc.religion.christian)
**Pipeline version:** v2
**Date:** 2026-03-22

---

## 1. Raw Data Policy

> **Rule #1:** `data/raw.csv` is never modified. All transformations write to `data/processed_v2/`.

The raw CSV contains the original parsed newsgroup messages with headers extracted during Lab 1.

---

## 2. What We Clean (`clean_text`)

| Artifact | Action | Reason |
|---|---|---|
| Newsgroup header lines (`From:`, `Subject:`, `Organization:`, etc.) | Remove entirely | Metadata, not content; would leak class signal in training |
| Quote lines starting with `>` | Remove | Cited text is noise from other authors |
| `In article <…>` citation headers | Remove | Structural artifact, not content |
| Email signature blocks (`--` delimiter) | Remove | Author contact info is noise |
| Forwarded-message wrappers (`--- Original Message ---`) | Remove | Redundant nested content |
| HTML tags (`<b>`, `<a>`, etc.) | Strip tags, keep inner text | Occasional HTML in 1990s newsgroup posts |
| HTML entities (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`) | Decode | Restore original characters |
| Multiple consecutive blank lines (3+) | Collapse to 2 | Preserve paragraph structure without excessive whitespace |
| Tabs and multiple spaces | Collapse to single space | Consistent tokenization |
| Leading/trailing whitespace | Strip per line and globally | Clean boundaries |

---

## 3. What We Normalize (`normalize_text`)

| Character / Pattern | Replacement | Example |
|---|---|---|
| Curly right apostrophe `'` (U+2019) | `'` (U+0027) | `it's` → `it's` |
| Curly left apostrophe `'` (U+2018) | `'` | same |
| Modifier letter apostrophe `ʼ` (U+02BC) | `'` | same |
| Curly double quotes `"` `"` | `"` | `"God"` → `"God"` |
| Guillemets `«` `»` | `"` | `«text»` → `"text"` |
| Em-dash `—` (U+2014) | `--` | `God—or not` → `God--or not` |
| En-dash `–` (U+2013) | `-` | `5V–12V` → `5V-12V` |
| Non-breaking space `\u00a0` | ` ` | Prevents invisible spacing issues |
| Unicode ellipsis `…` (U+2026) | `...` | Consistent representation |
| Cyrillic homoglyphs (а, е, о, р, с, х, у and uppercase) | Latin visuals | Prevent character-level confusion |

**NFC normalization** is applied first to decompose and recompose combining characters consistently.

---

## 4. What We Mask (`mask_pii`)

Masking is applied **after** cleaning and normalization so that markers like `<URL>`, `<EMAIL>`, `<PHONE>` survive all further steps.

| Entity | Token | Pattern |
|---|---|---|
| URLs (`http://`, `https://`, `ftp://`, `www.`) | `<URL>` | Regex: `https?://\S+\|www\.\S+\|ftp://\S+` |
| Email addresses | `<EMAIL>` | RFC 5322-simplified regex |
| US phone numbers (10-digit, various separators) | `<PHONE>` | `\b(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b` |

**Order:** URL before email (URLs sometimes contain `@`).

---

## 5. What We Do NOT Touch

| Item | Reason |
|---|---|
| Numbers and integers | Could be important identifiers or quantities |
| Version numbers (e.g., `1.2.3`, `2.0`) | Technical content, classifier may use them |
| Casing (UPPER/lower) | Preserving emphasis and proper nouns |
| Stopwords | Not removed at this stage (feature extraction decision) |
| Punctuation | Not stripped — needed for sentence splitting |
| Spelling errors | No spell-correction (determinism risk) |
| Technical abbreviations (IC, PCB, LED, MHz) | Domain terminology |

---

## 6. Sentence Splitting (`sentence_split`)

**Tool:** NLTK `sent_tokenize` with `language='english'` (Punkt tokenizer, pre-trained on English).

### Why NLTK Punkt?
- Pre-trained on English; handles most abbreviations out of the box (`Mr.`, `Dr.`, `Mrs.`, `Prof.`, `vs.`, `etc.`, `e.g.`, `i.e.`).
- Unsupervised model — no manual rules needed for standard cases.
- Fast and reproducible.

### Custom Protection for Version/Decimal Numbers
Before splitting, we temporarily mask:
- **Version numbers** like `1.2.3` → `__VER0__` (pattern: `\b\d+(?:\.\d+){2,}\b`)
- **Decimal numbers** like `3.14` → `__DEC0__` (pattern: `\b\d+\.\d+\b`)

After splitting, placeholders are restored. This prevents false sentence boundaries at dots in numbers.

### Abbreviations Handled by NLTK Punkt (English)

NLTK's English punkt model handles these out of the box: `Mr.`, `Mrs.`, `Ms.`, `Dr.`, `Prof.`, `vs.`, `etc.`, `e.g.`, `i.e.`, `Jan.`, `Feb.` and other month names, `St.`, `Ave.`, and more.

### Known Remaining Limitations
- Ambiguous abbreviations followed by a capital letter may still split (e.g., `St. Peter` — context-dependent). Accepted as-is.
- Very short sentences (1–2 words) may appear after removing quote lines. Filtered to non-empty strings only.

---

## 7. Before / After Examples

| # | Before | After | Step |
|---|---|---|---|
| 1 | `Contact support@example.com now.` | `Contact <EMAIL> now.` | mask_pii |
| 2 | `Visit https://gnu.org for info.` | `Visit <URL> for info.` | mask_pii |
| 3 | `Call 555-867-5309 anytime.` | `Call <PHONE> anytime.` | mask_pii |
| 4 | `>Previous poster wrote this.` | *(removed)* | clean_text |
| 5 | `From: user@host.com\nSubject: test\n\nBody text.` | `Body text.` | clean_text |
| 6 | `Main text.\n\n--\nJohn Smith` | `Main text.` | clean_text |
| 7 | `The price is &lt;$100 &amp; free shipping.` | `The price is <$100 & free shipping.` | clean_text |
| 8 | `He said \u201cbelieve\u201d in God.` | `He said "believe" in God.` | normalize_text |
| 9 | `It\u2019s working fine.` | `It's working fine.` | normalize_text |
| 10 | `5V\u201312V range` | `5V-12V range` | normalize_text |
| 11 | `God\u2014the creator\u2014exists.` | `God--the creator--exists.` | normalize_text |
| 12 | `See\u00a0attached.` | `See attached.` | normalize_text |
| 13 | `Firmware v1.2.3 released. Update now.` | Splits into 2 sentences at period after "released", NOT at "1.2.3" | sentence_split |
| 14 | `Mr. Smith said hello. She agreed.` | 2 sentences: `["Mr. Smith said hello.", "She agreed."]` | sentence_split |
| 15 | `Use resistors, etc. and diodes. Done.` | 2 sentences: `["Use resistors, etc. and diodes.", "Done."]` | sentence_split |

---

## 8. Pipeline Order

```
raw text
   │
   ▼
clean_text()        — remove artifacts, decode HTML, normalize whitespace
   │
   ▼
normalize_text()    — unicode normalization, quotes, dashes, homoglyphs
   │
   ▼
mask_pii()          — replace URLs / emails / phones with tokens
   │
   ▼
sentence_split()    — NLTK Punkt, number-aware
   │
   ▼
processed_v2 output
```

**Idempotence guarantee:** `preprocess(preprocess(x)["clean"])["clean"] == preprocess(x)["clean"]`
This holds because all substitutions are non-overlapping and their outputs are not re-matched by any pattern.

---

## 9. What Risks Remain After Lab 2

| Risk | Status |
|---|---|
| 17 exact duplicates in raw data | Still present in processed_v2 (deduplication is a downstream decision) |
| Very long texts (max ~11k words) | Not truncated — left for model training stage |
| Informal spelling / typos | Not corrected (out of scope for deterministic pipeline) |
| Cross-post content (threading artifacts) | Mostly removed via quote-line stripping |
| 1990s cultural/technological context | Cannot be fixed by preprocessing |
