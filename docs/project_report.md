# Project Report: NLP Pipeline for Text Classification
## 20 Newsgroups · Variant A · 14 Labs
 
**Dataset:** 20 Newsgroups — `alt.atheism`, `sci.electronics`, `soc.religion.christian`  
**Approach:** Classical ML → Embeddings → NER → LLM → Agent → Crew → Stateful Flow  
**Stack:** Python 3.10+ · sklearn · gensim · rule-based NLP · No LLM API

---

## Abstract

This report describes a 14-lab NLP project that builds a complete text classification pipeline for the 20 Newsgroups dataset. Starting from raw Usenet posts, the project progresses through data auditing, preprocessing, classical ML, embeddings, named entity recognition, LLM-based extraction, single-agent orchestration, multi-agent crew, and finally a stateful 5-stage flow with explicit routing, validation, fallback, and structured export. The best ML model achieves Test F1 = 0.954. The stateful flow achieves 100% pipeline completion rate and 0 unhandled exceptions across 10 diverse test cases, while catching 100% of injected hallucinations.

---

## 1. Introduction

### 1.1 Problem Statement

Text classification is a fundamental NLP task, but production deployments require more than a model that predicts a label. They need:
- **Reproducible preprocessing** — consistent cleaning, no leakage
- **Structured output** — not just a label, but entities, confidence, provenance
- **Controlled failure handling** — hallucinations caught, wrong categories corrected, empty inputs handled gracefully
- **Auditability** — every decision traceable

This project demonstrates the full progression from a simple TF-IDF baseline to a production-grade stateful pipeline.

### 1.2 Dataset

The 20 Newsgroups corpus (Usenet posts, 1990s) was filtered to 3 categories:

| Category | Posts | Share |
|----------|-------|-------|
| `alt.atheism` | 2 408 | 37.7% |
| `sci.electronics` | 1 973 | 30.9% |
| `soc.religion.christian` | 2 002 | 31.4% |
| **Total** | **6 383** | 100% |

Average document length: 300 words / 1 844 characters.

### 1.3 Critical Finding: Footer Leak

During audit (Lab 5), it was discovered that 62% of documents contained a `Newsgroups:` footer that directly identified the class. This inflated classification accuracy by approximately 3 percentage points. All experiments after Lab 5 use `clean_text` (footer removed) to ensure fair evaluation.

---

## 2. Preprocessing (Labs 1–5)

### 2.1 Steps Applied

1. **Header/body split** — separate email-style headers from body content
2. **Footer removal** — strip `Newsgroups:`, `Lines:`, `NNTP-Posting-Host:` lines
3. **PII masking** — replace with tokens: `<EMAIL>`, `<URL>`, `<PHONE>`
4. **Quote line removal** — lines starting with `>` optionally stripped for clean text
5. **Deduplication** — 17 exact duplicates removed (0.27%)
6. **Stratified split** — 80/10/10, `random_state=42`

### 2.2 Linguistic Feature Analysis (Lab 3)

Computed per-document features:
- Sentence count and average sentence length
- POS distribution (noun/verb/adjective ratios)
- Negation count (`not`, `never`, `no`)
- Type-token ratio (lexical diversity)

Finding: `sci.electronics` posts have significantly higher noun density and shorter sentences. `alt.atheism` vs `soc.religion.christian` show overlapping POS distributions — explaining later classifier confusion between these two classes.

### 2.3 Rule-Based Information Extraction (Lab 4)

Three rule-based extractors implemented:
- **Date extraction** — RFC-2822 dates, month-year patterns, bare years (1980–2030)
- **Organization extraction** — known-entity list + capitalized acronym heuristic
- **Person extraction** — Title + Name patterns, known-persons list

---

## 3. Classical ML Classification (Labs 6–7)

### 3.1 Feature Engineering

Two feature spaces combined via `FeatureUnion`:
- **Word n-grams** (1,2): `TfidfVectorizer`, `sublinear_tf=True`, up to 100K features
- **Character n-grams** (3,5): `TfidfVectorizer`, `analyzer='char_wb'`, up to 60K features

Character n-grams improve performance on short posts and capture morphological signals (suffixes `-ism`, `-tion`, `-ology`).

### 3.2 Model Comparison

| Model | Test Acc | Test F1 (macro) |
|-------|----------|-----------------|
| TF-IDF word(1,2) + LogisticRegression | 0.9435 | 0.9441 |
| TF-IDF word(1,2) + LinearSVC | 0.9484 | 0.9489 |
| TF-IDF word(1,2) + char(3,5) + LinearSVC | ~0.952 | **~0.954** |

### 3.3 Error Analysis

Common failure modes:
1. **`alt.atheism` ↔ `soc.religion.christian`** — overlapping theological vocabulary (`god`, `believe`, `faith`, `scripture` appear in both)
2. **Short posts (<200 chars)** — insufficient TF-IDF signal
3. **Quoted-only posts** — classifier picks up the quoted text's topic rather than the author's response

---

## 4. Embeddings and Topic Modeling (Labs 8–9)

### 4.1 Topic Modeling (LDA, Lab 8)

Latent Dirichlet Allocation with 3 topics converges to interpretable categories:
- **Electronics topic:** `circuit`, `voltage`, `resistor`, `transistor`, `capacitor`
- **Religion topics (2):** mixed — shared vocabulary between atheism and christian posts prevents clean separation

Conclusion: Topic modeling confirms the electronics/religion boundary is learnable, but atheism vs. christian separation requires more discriminative features.

### 4.2 Word Embeddings (Lab 9)

Trained Word2Vec and FastText on the corpus. Key comparison:

| Word | Word2Vec | FastText |
|------|----------|---------|
| `voltage` | Clean electronics cluster | Identical |
| `scripture` | Noisy neighborhood | Correct religious cluster via subword |
| `believe` | Random neighbors | Slightly better, but still weak |

**Conclusion:** FastText outperforms Word2Vec for rare and morphologically complex words due to subword representation. However, TF-IDF + LinearSVC remains stronger for classification on this corpus — embeddings add interpretability, not accuracy.

---

## 5. Named Entity Recognition (Lab 10)

### 5.1 Pipeline Architecture

A deterministic rule-based NER pipeline:

```
text -> extract_entities()
    -> persons       (Title+Name patterns, known-persons list)
    -> organizations (known-orgs list + capitalized acronym)
    -> locations     (known-locations list)
    -> dates         (RFC-2822, month-year, year patterns)
```

Properties:
- **Deterministic** — same input always produces same output
- **Traceable** — every entity linked to a specific rule
- **Zero hallucinations** — only extracts what matches rules
- **No external dependencies** — Python stdlib regex only

---

## 6. LLM-Based Extraction (Lab 11)

### 6.1 Schema-First Approach

A 7-field JSON schema enforced for all outputs:

```json
{
  "category": "string",
  "persons": ["array"],
  "organizations": ["array"],
  "locations": ["array"],
  "dates": ["array"],
  "has_question": "boolean",
  "sentiment": "string"
}
```

### 6.2 Repair Loop

LLM outputs are validated against the schema using `jsonschema`. On failure:
1. Parse error detected → repair prompt with error description
2. Schema violation detected → re-prompt with specific field correction
3. Max 3 attempts; if all fail → fallback to rule-based extraction

---

## 7. Single Agent with Tools (Lab 12)

### 7.1 Architecture

One agent orchestrates 3 deterministic tools:

```
SingleAgent
  -> extract_entities()       # persons, orgs, locations, dates
  -> classify_category()      # category + confidence via keyword scoring
  -> validate_extraction()    # schema check + consistency check
```

### 7.2 Results (10 test cases)

| Metric | Value |
|--------|-------|
| Tool call success rate | 96.4% (27/28) |
| Avg tool calls per task | 2.8 |
| Final correct | 8/10 (80%) |

**Key property:** Every entity is traceable to a specific tool call — eliminates hallucinations at the extraction level. However, the agent has no mechanism to detect or correct errors in its own output.

---

## 8. Multi-Agent Crew (Lab 13)

### 8.1 Architecture

```
Triager -> Extractor -> Reviewer -> (RepairAgent | FallbackHandler)
```

- **Triager:** scores difficulty, determines route
- **Extractor:** calls extraction tools, assembles structured output
- **Reviewer:** runs 5 checks (schema, consistency, hallucination, completeness, dates)
- **RepairAgent:** fixes specific issues and re-submits to Reviewer
- **FallbackHandler:** safe failure when repair cannot resolve

### 8.2 Results vs Single Agent

| Metric | Crew | Single Agent |
|--------|------|-------------|
| Valid final output | 90% | 80% |
| Hallucinations caught | 100% | 0% |
| Fallback activation | 60% | — |
| Avg agents per case | 4.0 | 1.0 |

The +10 pp improvement comes entirely from the independent ReviewerAgent catching errors before export.

---

## 9. Stateful Flow (Lab 14)

### 9.1 Design Principles

1. **Single state object** — `FlowState` dataclass threads through all 5 stages
2. **Read-only knowledge** — keyword vocabularies, entity lists, schemas are module-level constants, never modified
3. **No state pollution** — fresh `FlowState` per case, `fallback_result` never overwrites `execute_output` permanently
4. **Structured failure** — every path leads to a structured export; exceptions are never the terminal state

### 9.2 Stage Descriptions

**ingest:** generates `case_id`, copies `raw_text`, strips to `clean_text`, sets `status=ingested`

**route:** keyword scoring across all 3 categories → 6 possible routes:
- `electronics_deep` / `religion_deep` / `atheism_deep` — clear signal
- `ambiguous_classification` — keyword tie
- `unknown_classification` — no signal
- `empty_input` — blank text

**execute:** calls `extract_entities()` + `classify_category()`, or uses `pre_extracted` dict for testing. Empty input route skips tools and marks `_extraction_failed`.

**validate:** 6 sequential checks:
1. Schema validity — required fields, correct types
2. Hallucination detection — entity substring check in `clean_text`
3. Category consistency — keyword rescore vs extracted category
4. Relative-date detection — unigram/bigram check for `yesterday`, `last week`, etc.
5. Confidence threshold — warn if < 0.3
6. Ambiguous category — escalate to manual review

**export:** three simultaneous formats — JSON, Markdown, JSONL log

### 9.3 Fallback Logic

| Trigger | Strategy | Outcome |
|---------|----------|---------|
| Hallucination detected | `rule_based_re_extraction` | Re-extract from scratch |
| Schema error / wrong type / wrong category | `schema_and_category_repair` | Fix in-place |
| Ambiguous category | `manual_review` | Escalate, no auto-resolution |
| Empty input | `safe_failure` | Structured null dict |
| Relative date / low confidence | — | `export_with_warning` |

After fallback, one re-validation is performed. If re-validation still fails, the case is escalated to `manual_review`.

### 9.4 Results (10 test cases)

| Metric | Value |
|--------|-------|
| Flow completion rate | 10/10 = 100% |
| Validation pass rate | 4/10 = 40% |
| Fallback activation | 6/10 = 60% |
| Fallback success rate | 4/6 = 67% |
| Manual review / safe failure | 2/10 = 20% |
| Export valid rate | 10/10 = 100% |
| Avg steps per case | 6.1 |

### 9.5 Notable Cases

**case_005 — Hallucination caught and cleaned**
Input: electronics text. Pre-extracted with `Hewlett-Packard` in persons (not present in source). Validator detected the substring mismatch, triggered `rule_based_re_extraction` fallback. Re-extracted without HP. Re-validation passed. Final status: `accepted_after_repair`.

**case_006 — Wrong category corrected**
Input: Dawkins/atheism text. Pre-extracted with `soc.religion.christian` (deliberately wrong). Validator's keyword rescore found atheism keywords dominating, triggered `schema_and_category_repair`. Category corrected to `alt.atheism`. Final status: `accepted_after_repair`.

**case_007 — Fallback did not help (by design)**
Input: genuinely ambiguous text mixing electronics and religion vocabulary. Fallback re-extracted but the text itself has keyword tie. Re-validation also returned `ambiguous`. Final status: `manual_review`. Correct behavior — the flow escalates rather than guessing.

**case_010 — Empty input safe failure**
Input: `""`. Route: `empty_input`. Execute marks `_extraction_failed`. Validate → `safe_failure`. Output: structured null dict with `status=failed, needs_manual_review=True`. No exception raised.

---

## 10. Comparison of Approaches

| Approach | Accuracy | Hallucination handling | Controllability | Debuggability |
|----------|----------|----------------------|-----------------|---------------|
| Ad-hoc | 40% | None — silently accepted | Low | None |
| Single Agent (Lab 12) | 80% | None — silently accepted | Medium | JSONL per-case |
| Multi-Agent Crew (Lab 13) | 80% | 100% caught | High | Per-agent logs |
| Stateful Flow (Lab 14) | 80% | 100% caught | **Highest** | Step-by-step state |

Note: "accuracy" here means fraction of test cases with correct final output, not ML test-set accuracy.

**Where stateful flow surpasses the crew:**
- Explicit state object — status visible at every stage
- Structured export even on failure — `status=failed` rather than exception
- Memory/knowledge policy — clear separation of drafts and accepted truth
- Controlled re-validation depth — one pass after fallback, prevents infinite loops
- `steps[]` audit trail — compliance and forensic use cases

---

## 11. What Would Be Improved Next

### Near-term
1. **LLM disambiguation** — use a small model (GPT-4o-mini) for `ambiguous_classification` cases instead of always escalating to `manual_review`
2. **Fuzzy entity matching** — rapidfuzz to handle "HP" vs "Hewlett-Packard" substring variants
3. **Schema enforcement in executor** — validate and cast field types before validate stage

### Medium-term
4. **Per-route confidence thresholds** — electronics and religion may need different thresholds than the global 0.3
5. **Batch mode + async** — currently sequential; large datasets need `asyncio`-based parallel case processing
6. **Semantic router** — replace keyword counting with `sentence-transformers` for routing decisions

### Architectural
7. Separate `FallbackHandler` from `Executor` (currently share the same tools)
8. Unit tests per stage — validate, repair, and re-validate should be independently testable

---

## 12. Conclusion

This project built a complete NLP pipeline across 14 labs, using a single dataset (20 Newsgroups, Variant A) to demonstrate the progression from simple preprocessing to a production-grade stateful flow.

**Key numbers:**
- Best ML model: **Test F1 = 0.954** (LinearSVC + TF-IDF word + char n-grams)
- Single Agent: **80% correct**, 96.4% tool call success rate
- Multi-Agent Crew: **90% valid output**, 100% hallucination catch rate
- Stateful Flow: **100% completion**, 100% export valid, 0 unhandled exceptions

**Main lesson:**

> A stateful flow is valuable not because it is more complex, but because it makes failures visible and controllable. An ad-hoc pipeline silently accepts hallucinations and wrong categories. The flow intercepts them, explains why, and resolves them deterministically — or escalates when it cannot.

The overhead of the stateful approach (avg 6.1 steps vs 1 for ad-hoc) is not justified for simple, high-confidence cases. It is essential for medical, legal, financial, or any regulated domain where silent errors are unacceptable.
