# NLP Pipeline: від сирих даних до stateful flow

**20 Newsgroups · Text Classification (Variant A) · 14 лабораторних робіт**

> Повний NLP pipeline — від збору та очистки сирих даних до stateful агентної системи з валідацією, fallback та structured export. Python stdlib, без LLM API.

---

## Pipeline

```
Raw data
  -> Preprocessing   (PII masking, footer removal, dedup)
  -> ML Baseline     (TF-IDF + LinearSVC, F1 = 0.954)
  -> Embeddings      (Word2Vec, FastText, LDA topics)
  -> NER             (rule-based: persons, orgs, dates)
  -> LLM Extraction  (schema-first, repair loop)
  -> Single Agent    (tool-grounded, 80% correct)
  -> Multi-Agent Crew(Triager -> Extractor -> Reviewer, 90% valid)
  -> Stateful Flow   (5-stage, 100% completion, 0 unhandled errors)
```

---

## Dataset

| Parameter | Value |
|-----------|-------|
| Source | 20 Newsgroups (sklearn / Kaggle) |
| Documents | 6 383 |
| Language | English (Usenet, 1990s) |
| Classes | `alt.atheism` (37.7%) · `sci.electronics` (30.9%) · `soc.religion.christian` (31.4%) |
| Avg length | 300 words / 1 844 chars |
| Split | 80/10/10, stratified, seed=42 |

**Key audit finding:** `Newsgroups:` footer was present in 62% of documents and leaked the class label — artificially inflating accuracy by ~3 pp. All experiments use `clean_text` (footer removed).

---

## Results by Lab

| Labs | Topic | Key Result |
|------|-------|------------|
| 1–2 | Data collection & cleaning | Footer leak detected, PII masked, 17 duplicates removed |
| 3 | Linguistic features | POS distribution, negation count, sentence length features |
| 4 | Rule-based IE | Date, org, person extraction via regex + known-entity lists |
| 5 | Split & leakage audit | Stratified 80/10/10 confirmed, footer-free baseline established |
| 6 | TF-IDF + LogReg baseline | Test Acc 0.9435, Macro F1 0.9441 |
| 7 | LinearSVC + char-ngrams | **Test F1 0.954** — best model |
| 8 | Topic Modeling (LDA) | 3 topics map cleanly to 3 categories |
| 9 | Word2Vec / FastText | FastText better for rare/morphologically complex words |
| 10 | Hybrid NER pipeline | Rule-based, deterministic, 0 hallucinations |
| 11 | LLM schema-first extraction | 7-field JSON schema, repair loop for schema errors |
| 12 | Single Agent + tools | 80% correct, 96.4% tool success rate |
| 13 | Multi-Agent Crew | 90% valid output, **100% hallucination catch rate** |
| 14 | Stateful Flow | **100% completion, 100% export valid, 0 unhandled exceptions** |

---

## Stateful Flow (Lab 14)

5-stage pipeline with explicit state, routing, validation, fallback, and structured export.

```
ingest -> route -> execute -> validate -> export
                                 |
                    accept       -> exported
                    export_warn  -> exported_with_warning
                    repair       -> fix -> re-validate -> accepted_after_repair
                    fallback     -> re-extract -> re-validate
                    manual_review-> escalate (no auto-resolution)
                    safe_failure -> status=failed (structured null, no exception)
```

**Metrics (10 test cases):**

| Metric | Value |
|--------|-------|
| Flow completion rate | 10/10 = 100% |
| Validation pass rate | 4/10 = 40% |
| Fallback activation | 6/10 = 60% |
| Fallback success rate | 4/6 = 67% |
| Export valid rate | 10/10 = 100% |
| Avg steps per case | 6.1 |

**What flow improves vs ad-hoc:**

| Scenario | Ad-hoc | Stateful Flow |
|----------|--------|---------------|
| Hallucination | Accepted silently | Caught + removed |
| Wrong category | Not detected | Caught + corrected |
| Schema error | Crash or ignored | Detected + repaired |
| Relative date | Ignored | Flagged with warning |
| Ambiguous result | Picks wrong winner | Escalated to manual review |
| Empty input | Exception | Structured safe-failure |
| Debugging | No visibility | Step-by-step audit trail |

---

## Notebooks

| Notebook | Description | Colab |
|----------|-------------|-------|
| `final_demo.ipynb` | **End-to-end demo** — preprocessing, ML, NER, flow | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/final_demo.ipynb) |
| `lab6_tfidf_logistic_baseline.ipynb` | TF-IDF + LogReg baseline | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/lab6_tfidf_logistic_baseline.ipynb) |
| `lab7_linear_svm_char_ngrams.ipynb` | LinearSVC + char-ngrams | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/lab7_linear_svm_char_ngrams.ipynb) |
| `lab12_tool_grounded_single_agent.ipynb` | Single agent | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/lab12_tool_grounded_single_agent.ipynb) |
| `lab13_multi_agent_crew_*.ipynb` | Multi-agent crew | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/lab13_multi_agent_crew_triager_extractor_reviewer.ipynb) |
| `lab14_flow_orchestration_*.ipynb` | Stateful flow | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DanylchenkoKateryna/NLP-Lab-works/blob/main/notebooks/lab14_flow_orchestration_crewai_flows.ipynb) |

---

## Project Structure

```
.
├── src/
│   ├── tools.py           # extract_entities(), classify_category(), validate_extraction()
│   ├── flow_state.py      # FlowState dataclass — single source of truth
│   ├── router.py          # route_step() — 6 routes based on keyword scoring
│   ├── executor.py        # execute_step() — calls tools, supports pre_extracted
│   ├── exporter.py        # export_step() — JSON + Markdown + CSV
│   ├── flow_logger.py     # JSONL logging, one line per case
│   ├── flow.py            # NLPFlow orchestrator — full 5-stage pipeline
│   └── eval_flow.py       # 10 test cases + metrics + ad-hoc baseline
│
├── notebooks/
│   ├── final_demo.ipynb               # end-to-end demo (this file)
│   ├── lab14_flow_orchestration_*.ipynb
│   └── lab{2-13}_*.ipynb
│
├── docs/
│   ├── project_report.md              # full project report
│   ├── final_presentation.pptx        # slides (14 labs)
│   ├── flow_logs_lab14.jsonl          # JSONL log — 10 test cases
│   ├── audit_summary_lab14.md
│   ├── memory_policy_lab14.md
│   └── ...
│
├── labs/
│   └── lab{01-14}/README.md           # per-lab documentation
│
└── README.md
```

---

## Running Locally

```bash
# Clone
git clone https://github.com/DanylchenkoKateryna/NLP-Lab-works.git
cd NLP-Lab-works

# No extra install needed for the flow (stdlib only)
# For ML labs: pip install scikit-learn gensim

# Run the stateful flow directly
PYTHONUTF8=1 python -c "
import sys; sys.path.insert(0, 'src')
from flow import NLPFlow
flow = NLPFlow()
state = flow.run('The capacitor stores 10 microfarads at 16V. Measured by John in March 1993.')
print(state.status, state.final_output)
"

# Run all 10 test cases
PYTHONUTF8=1 python -c "
import sys; sys.path.insert(0, 'src')
from eval_flow import run_all_cases, compute_flow_metrics, print_metrics
results = run_all_cases()
print_metrics(compute_flow_metrics(results))
"
```

---

## Tech Stack

- **Language:** Python 3.10+ (stdlib only for flow)
- **ML:** scikit-learn (TF-IDF, LinearSVC, LogisticRegression)
- **Embeddings:** gensim (Word2Vec, FastText), sklearn (LDA)
- **NER:** rule-based (regex + known-entity lists)
- **Agents:** custom Python classes (no framework dependency)
- **No LLM API** required

---

## Key Takeaway

> Stateful flow is valuable not because it is more complex,  
> but because it makes failures **visible and controllable**.  
> An ad-hoc pipeline silently accepts hallucinations and wrong categories.  
> The flow intercepts, explains, and resolves them deterministically.
