# Extraction Schema — Lab 11

## 1. Extraction Task

**Corpus**: 20 Newsgroups (alt.atheism, sci.electronics, soc.religion.christian)
**Task**: From a post fragment, extract 7 structured fields (schema-first approach).
**Use case**: Structured indexing for downstream retrieval / filtering / clustering.

---

## 2. Fields in JSON Output

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `category` | string (enum) | ✅ | Which newsgroup |
| `persons` | array[string] | ✅ | Named person mentions |
| `organizations` | array[string] | ✅ | Org / company names |
| `locations` | array[string] | ✅ | Location / GPE names |
| `dates` | array[string] | ✅ | Date strings verbatim |
| `has_question` | boolean | ✅ | Post contains question? |
| `sentiment` | string (enum) | ✅ | Overall tone |

---

## 3. Required Fields

All 7 fields are required. Missing any field → schema_violation.

---

## 4. JSON Schema (formal)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["category","persons","organizations","locations","dates","has_question","sentiment"],
  "properties": {
    "category":      {"type": "string", "enum": ["sci.electronics","soc.religion.christian","alt.atheism"]},
    "persons":       {"type": "array",  "items": {"type": "string"}},
    "organizations": {"type": "array",  "items": {"type": "string"}},
    "locations":     {"type": "array",  "items": {"type": "string"}},
    "dates":         {"type": "array",  "items": {"type": "string"}},
    "has_question":  {"type": "boolean"},
    "sentiment":     {"type": "string", "enum": ["positive","negative","neutral","mixed"]}
  },
  "additionalProperties": false
}
```

---

## 5. Rules for null / missing values

- **Arrays** — if nothing to extract, return `[]` (empty array), **not** `null`
- **category** — always infer from context; must match exactly one enum value
- **has_question** — must be boolean `true`/`false`, **not** string `"true"` or `"false"`
- **sentiment** — if ambiguous, use `"mixed"`

---

## 6. Most Problematic Fields

| Field | Failure Mode | Frequency |
|-------|-------------|-----------|
| `has_question` | String `"false"` instead of boolean `false` | 1/20 |
| `category` | Incorrect enum value (`"atheism"` not `"alt.atheism"`) | 1/20 |
| `sentiment` | Missing (field omitted by LLM) | 1/20 |
| `dates` | Religious terms like `"Pentecost"` included as dates | semantic |
| `organizations` | Missing ORGs when only acronym is used | semantic |

---

## 7. What Repair Loop Fixes

| Error Type | Repair Success | Notes |
|-----------|----------------|-------|
| Code fence wrapping (`\`\`\`json`) | ✅ Fixed | Repair prompt strips fences |
| Trailing text after JSON | ✅ Fixed | Repair prompt enforces JSON-only |
| Missing required field | ✅ Fixed | Repair prompt names the missing field |
| Wrong type (boolean as string) | ✅ Fixed | Repair prompt specifies types |
| Enum violation | ✅ Fixed | Repair prompt repeats allowed values |
| Not JSON at all | ❌ Not fixed | Some LLM responses are unfixable |
