# Lab 1 — Data Collection & Audit

## Task

**Type:** A — Text Classification
**Text field:** `text` — body of a Usenet newsgroup message (English, 1990s)
**Target:** 3-class classification — `alt.atheism`, `sci.electronics`, `soc.religion.christian`

## Dataset

| Parameter | Value |
|---|---|
| Source | 20 Newsgroups (Kaggle / `sklearn.datasets`) |
| Total documents | 6,383 |
| Language | English |
| Format | Text files with headers + body |
| License | Public Domain |

**Class distribution:**

| Class | Count | % |
|---|---|---|
| alt.atheism | 2,405 | 37.7% |
| sci.electronics | 1,975 | 30.9% |
| soc.religion.christian | 2,003 | 31.4% |

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place raw data in uploads/
#    alt.atheism.txt, sci.electronics.txt, soc.religion.christian.txt

# 3. Run audit script
python notebooks/lab1_data_audit.py
```

Outputs: `data/raw.csv`, `data/processed_v1/processed.csv`, `data/labels.csv`

## Processing Applied

- Header/body parsing (split on `From:` markers)
- Whitespace normalization and apostrophe unification
- URL / email / phone masking → `<URL>`, `<EMAIL>`, `<PHONE>`

## Key Findings

| Metric | Value |
|---|---|
| Mean char length | 1,844 |
| Mean word count | 300 |
| Exact duplicates | 17 (0.27%) |
| Very short texts (<5 words) | 10 (0.16%) |
| Emails found | 5,306 |
| Phones found | ~500 |

## Identified Risks

1. Very long texts (max ~11,000 words) — may require truncation
2. Informal 1990s internet language with typos and abbreviations
3. Nested quote citations create noise in the body text
4. Technical (electronics) and religious domain terminology
5. Low but non-zero duplicate rate (0.27%)
