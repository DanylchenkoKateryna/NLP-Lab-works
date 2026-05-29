# Lab 11 — LLM Extraction as Engineering (schema-first)

## Extraction Case

**Task**: Structured extraction from 20 Newsgroups post fragments
**Corpus**: 20 Newsgroups — alt.atheism, sci.electronics, soc.religion.christian
**Evaluation set**: 20 texts (9 sci.electronics + 6 soc.religion.christian + 5 alt.atheism)

---

## Schema (7 fields)

| Field | Type | Constraint |
|-------|------|-----------|
| `category` | string | enum: sci.electronics / soc.religion.christian / alt.atheism |
| `persons` | array[string] | empty `[]` if none |
| `organizations` | array[string] | empty `[]` if none |
| `locations` | array[string] | empty `[]` if none |
| `dates` | array[string] | verbatim from text, `[]` if none |
| `has_question` | boolean | must be `true`/`false`, not string |
| `sentiment` | string | enum: positive / negative / neutral / mixed |

Full formal JSON Schema in `docs/extraction_schema_lab11.md` and `src/json_schema.py`.

---

## Baseline Extraction Prompt

```
You are an information extraction system for 20 Newsgroups posts.
Extract structured information from the text below.

Return ONLY a valid JSON object with EXACTLY these fields:
  "category"      : one of ["sci.electronics", "soc.religion.christian", "alt.atheism"]
  "persons"       : array of person names mentioned (use [] if none)
  ...
  "has_question"  : boolean true if text contains a question, false otherwise
  "sentiment"     : one of ["positive", "negative", "neutral", "mixed"]

Rules:
1. If a value is not present, use [] for arrays
2. Return ONLY the JSON object — no markdown, no code fences, no explanation
3. Do NOT add any text before or after the JSON

TEXT: {text}
JSON:
```

---

## Validator

Two-step validation (`src/validator.py`):
1. `json.loads()` — parse check (catches code fences, trailing text, not-JSON)
2. `jsonschema.validate()` — schema check (catches missing fields, wrong types, enum violations)

Reports separate `parse_error` vs `schema_violation` categories.

---

## Repair Loop

`src/repair_loop.py` — max 2 total attempts (1 raw + 1 repair):

1. Run extraction prompt → raw output
2. Validate → if valid, done
3. If invalid → build repair prompt (broken output + error message + instructions)
4. Call LLM again → validate repair output
5. Accept or mark as permanently failed

---

## Valid JSON Rate

| Metric | Value |
|--------|-------|
| Raw valid JSON rate | 14 / 20 = **70.0%** |
| Post-repair valid JSON rate | 19 / 20 = **95.0%** |
| Schema-valid JSON rate | 19 / 20 = **95.0%** |
| Repair needed | 6 / 20 = 30.0% |
| Repair fixed | 5 / 6 = 83.3% |

---

## Remaining Problems

- **`not_json`** (1/20): LLM returns natural-language summary; repair prompt also fails — permanently unfixable by repair loop
- **Semantic**: `"Pentecost"` classified as a date string (technically in `dates[]` but not a standard date)
- **Schema gap**: electronics part names (transistor, resistor) have no dedicated field — lost information
- **Normalization**: LLM uses "Farnell Electronics" vs gold "Farnell" — string-level mismatch

## Files

| File | Description |
|------|-------------|
| `notebooks/lab11_llm_extraction_schema_first.ipynb` | Main notebook |
| `src/json_schema.py` | EXTRACTION_SCHEMA + get_schema() |
| `src/validator.py` | Two-step validation + ValidationResult |
| `src/llm_extract.py` | MockLLM + prompt builders + EVAL_TEXTS |
| `src/repair_loop.py` | extract_with_repair + pipeline_metrics |
| `docs/extraction_schema_lab11.md` | Schema documentation |
| `docs/audit_summary_lab11.md` | Auto-generated audit summary |
