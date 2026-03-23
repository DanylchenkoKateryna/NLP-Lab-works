# Lab 4 — Rule-Based Information Extraction

**Corpus:** 20 Newsgroups — `alt.atheism` / `sci.electronics` / `soc.religion.christian`
**Task:** A — Text Classification
**Method:** Regex + dictionaries (no LLM/ML)

---

## 1. Three field types extracted

| Field Type | Description | Corpus frequency |
|---|---|---|
| **DATE** | Calendar dates with month names or ISO format | ~494 in full corpus |
| **ELEC_QTY** | Electrical/physical quantities with units (V, A, Hz, Ω, W, F, H, dB) | ~1,317 in full corpus |
| **SCRIPTURE_REF** | Bible / Quran verse references (Book Chapter:Verse) | ~1,468 in full corpus |

---

## 2. Rules and dictionaries used

- **DATE** — 4 regex patterns: ISO (`YYYY-MM-DD`), US slash (`MM/DD/YY`), month-day-year (`Jan 3, 1993`), day-month-year (`16 May 1993`). Month names resolved via `resources/months_en.json`.
- **ELEC_QTY** — single regex with 10+ unit alternations; `resources/elec_units.json` maps abbreviations to canonical unit + type. Anti-rule: reject if immediately preceded by a letter (blocks part numbers like `1615A`).
- **SCRIPTURE_REF** — regex built dynamically from `resources/bible_books.json` aliases (sorted longest-first). Supports abbreviated book names, numbered prefixes (`1 Cor`, `II Pet`), and roman numeral normalisation. Anti-rule: require explicit colon/dot separator for ambiguous single-word names (`John`, `Mark`, `Luke`).
- **Common** — `extract_all(text)` returns all three types in one call; each entity carries `start_char`, `end_char`, `method` for full auditability.

---

## 3. Precision by field type

Results on gold subset (`data/sample/lab4_gold_ie.jsonl`, 120 entries, 64 texts):

| Field Type | Precision | Notes |
|---|---|---|
| DATE | see `docs/audit_summary_lab4.md` | ISO + month-name patterns are conservative |
| ELEC_QTY | see `docs/audit_summary_lab4.md` | Part-number anti-rule eliminates main FP class |
| SCRIPTURE_REF | see `docs/audit_summary_lab4.md` | Separator-guard reduces person-name collisions |

---

## 4. Top-5 edge cases in this corpus

1. **`32kHz`** — no space between number and unit; regex allows zero whitespace.
2. **`1 Corinthians 11.26`** — period as chapter-verse separator and numeric book prefix; both handled.
3. **`1615A`** — HP logic analyser model number; rejected by the "preceded by alpha" anti-rule.
4. **`16 may 1993`** — lowercase month in DMY order; case-insensitive regex + `lower()` lookup.
5. **`John Smith`** — person name that matches book alias; suppressed because no `:`/`.` verse separator.

---

## 5. Planned improvements

- Add **year-only DATE** support with explicit context keywords (`"in 1985"`, `"since 1993"`).
- Extend ELEC_QTY to handle **signed values** (`+14 dB`) and **ranges** (`150–200 ohms`) as single entities.
- Add **ROMAN_NUMERAL** book prefix normalisation for edge cases like `III John`.
- Integrate ELEC_QTY with **unit conversion** (store both raw and SI-base value).
- Increase gold subset to 200+ entries with true manual validation for reliable recall estimation.

---

## How to run

```bash
# Local
cd <repo-root>
python -m jupyter nbconvert --to notebook --execute notebooks/lab4_rule_based_ie.ipynb
```

Or open `notebooks/lab4_rule_based_ie.ipynb` in Google Colab and click **Run all**.

## Key files

| Path | Description |
|---|---|
| `src/ie_rules.py` | Core extractor (DATE, ELEC_QTY, SCRIPTURE_REF) |
| `resources/months_en.json` | Month name → number mapping |
| `resources/elec_units.json` | Unit abbreviation → canonical + type |
| `resources/bible_books.json` | Bible book canonical names |
| `docs/ie_policy.md` | Field-type specification + negative examples |
| `data/sample/lab4_gold_ie.jsonl` | Gold evaluation subset |
| `tests/ie_edge_cases.jsonl` | 30 edge case regression tests |
| `docs/audit_summary_lab4.md` | Auto-generated precision report |
