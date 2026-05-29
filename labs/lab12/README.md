# Lab 12 — Tool-grounded Single Agent

## 1. Use Case
**NLP Research Post Analyzer** — structured extraction from 20 Newsgroups posts.

## 2. Agent Task
One agent, three tools, full logging.
Input: raw text → Output: structured JSON with category + entities + validation.

## 3. Tools
| Tool | File | Purpose |
|------|------|---------|
| `extract_entities` | `src/tools.py` | Regex + keyword NER |
| `classify_category` | `src/tools.py` | Keyword-score classifier |
| `validate_extraction` | `src/tools.py` | Schema + consistency check |

## 4. Running the Notebook
**Colab**: Open badge at top of notebook → Run all (no configuration needed)
**Local**: `cd repo-root && jupyter notebook notebooks/lab12_tool_grounded_single_agent.ipynb`

## 5. Logs
- `docs/tool_logs_lab12.jsonl` — all tool call logs (JSONL, one entry per line)
- Generated automatically by notebook cell 9

## 6. Test Cases
10 cases covering all required scenarios:
1. Simple clear case
2. Missing data
3. Noisy text
4. Empty result
5. Unnecessary tool
6. Ambiguous category
7. Two tools sequential
8. Validator finds problem
9. Answer relies on tool output
10. Tool fails (empty input)

## 7. Metrics
| Metric | Value |
|--------|-------|
| Tool call success rate | 96.4% (27/28) |
| Avg calls per task | 2.8 |
| Tasks where tools helped | 5/10 = 50% |
| Unnecessary tool calls | 1 |
| Final correct | 8/10 = 80% |
| Final partly correct | 1/10 |
| Final wrong / error | 1/10 |

## 8. Main Conclusion
Schema-first tool-grounded agents eliminate hallucinations for entity extraction
and provide structured, auditable outputs. The key win is that tools are
**deterministic and logged** — every entity in the final answer is traceable
to a specific tool call. The main limitation is that keyword-based tools break
on noisy/misspelled text and cannot handle semantic ambiguity.
