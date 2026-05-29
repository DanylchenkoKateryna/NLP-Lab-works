"""
repair_loop.py — Extraction + validation + repair loop.

Logic
-----
1. Call LLM (attempt 0) — raw extraction
2. Validate: parse JSON → check schema
3. If invalid → build repair prompt → call LLM (attempt 1)
4. Validate repair output
5. Max 2 total attempts (1 raw + 1 repair)
6. Return final result with full trace
"""

from __future__ import annotations
from dataclasses import dataclass, field

try:
    from llm_extract import BaseLLM, build_extraction_prompt, build_repair_prompt, EVAL_TEXTS
    from validator import validate_output, ValidationResult
except ImportError:
    from src.llm_extract import BaseLLM, build_extraction_prompt, build_repair_prompt, EVAL_TEXTS
    from src.validator import validate_output, ValidationResult


MAX_REPAIR_ATTEMPTS = 1   # max retries after the first failure


@dataclass
class ExtractionResult:
    """Full trace of a single extraction run."""
    text_idx:        int
    text:            str
    raw_response:    str
    raw_valid:       ValidationResult = field(default=None)   # type: ignore
    repaired:        bool = False
    repair_response: str | None = None
    repair_valid:    ValidationResult = field(default=None)   # type: ignore
    final_valid:     ValidationResult = field(default=None)   # type: ignore
    n_attempts:      int = 1

    @property
    def success(self) -> bool:
        return self.final_valid is not None and self.final_valid.valid

    @property
    def needed_repair(self) -> bool:
        return self.repaired

    @property
    def repair_helped(self) -> bool:
        return self.repaired and self.final_valid.valid

    def summary_line(self) -> str:
        status = "VALID" if self.success else "INVALID"
        mark   = "\u2713" if self.success else "\u2717"
        repair = f" (repaired {'OK' if self.repair_helped else 'FAIL'})" if self.repaired else ""
        return (
            f"[{self.text_idx:02d}] {mark} {status}{repair}"
            f"  parse={'OK' if self.final_valid.parse_ok else 'FAIL'}"
            f"  schema={'OK' if self.final_valid.schema_ok else 'FAIL'}"
            f"  err={self.final_valid.short_error()}"
        )


def extract_with_repair(
    llm: BaseLLM,
    text: str,
    text_idx: int,
) -> ExtractionResult:
    """
    Run extraction + repair loop for a single text.

    Steps
    -----
    1. Build extraction prompt
    2. Call LLM (attempt=0) → raw response
    3. Validate raw response
    4. If valid → done
    5. If invalid → build repair prompt → call LLM (attempt=1)
    6. Validate repair → done regardless
    """
    prompt = build_extraction_prompt(text)
    raw    = llm.call(prompt, text_idx=text_idx, attempt=0)
    rv     = validate_output(raw)

    result = ExtractionResult(
        text_idx=text_idx,
        text=text,
        raw_response=raw,
        raw_valid=rv,
        final_valid=rv,
        n_attempts=1,
    )

    if rv.valid:
        return result

    # Repair attempt
    error_msg     = rv.parse_error if not rv.parse_ok else (rv.first_schema_error() or "schema validation failed")
    repair_prompt = build_repair_prompt(text, raw, error_msg)
    repair_resp   = llm.call(repair_prompt, text_idx=text_idx, attempt=1)
    repair_rv     = validate_output(repair_resp)

    result.repaired        = True
    result.repair_response = repair_resp
    result.repair_valid    = repair_rv
    result.final_valid     = repair_rv
    result.n_attempts      = 2

    return result


def run_pipeline(
    llm: BaseLLM,
    texts: list[str] | None = None,
) -> list[ExtractionResult]:
    """
    Run extraction + repair loop over a list of texts.

    Parameters
    ----------
    llm   : LLM client (MockLLM or real)
    texts : list of input strings; defaults to EVAL_TEXTS
    """
    if texts is None:
        texts = EVAL_TEXTS
    return [extract_with_repair(llm, t, i) for i, t in enumerate(texts)]


def pipeline_metrics(results: list[ExtractionResult]) -> dict:
    """
    Compute valid-JSON-rate metrics from a list of ExtractionResult.

    Returns
    -------
    dict with keys matching the lab metric requirements:
      total, raw_valid, raw_valid_rate,
      needed_repair, repair_fixed, repair_fixed_rate,
      post_repair_valid, post_repair_valid_rate,
      final_invalid, avg_attempts
    """
    n             = len(results)
    raw_valid     = sum(1 for r in results if r.raw_valid.valid)
    needed_repair = sum(1 for r in results if r.needed_repair)
    repair_fixed  = sum(1 for r in results if r.repair_helped)
    post_valid    = sum(1 for r in results if r.success)
    total_att     = sum(r.n_attempts for r in results)

    return {
        "total":                n,
        "raw_valid":            raw_valid,
        "raw_valid_rate":       round(raw_valid / n, 4) if n else 0.0,
        "needed_repair":        needed_repair,
        "repair_fixed":         repair_fixed,
        "repair_fixed_rate":    round(repair_fixed / needed_repair, 4) if needed_repair else 1.0,
        "post_repair_valid":    post_valid,
        "post_repair_valid_rate": round(post_valid / n, 4) if n else 0.0,
        "final_invalid":        n - post_valid,
        "avg_attempts":         round(total_att / n, 3) if n else 1.0,
        "pct_needed_repair":    round(needed_repair / n * 100, 1),
        "pct_repair_failed":    round((needed_repair - repair_fixed) / n * 100, 1),
    }


def print_pipeline_metrics(metrics: dict, label: str = "Pipeline") -> None:
    """Pretty-print the pipeline metrics table."""
    m = metrics
    sep = "-" * 50
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")
    print(f"  Total examples              : {m['total']}")
    print(sep)
    print(f"  Raw valid JSON rate         : {m['raw_valid']:2d} / {m['total']}  = {m['raw_valid_rate']*100:.1f}%")
    print(sep)
    print(f"  Needed repair               : {m['needed_repair']:2d} / {m['total']}  = {m['pct_needed_repair']:.1f}%")
    print(f"  Repair fixed                : {m['repair_fixed']:2d} / {m['needed_repair']}   = {m['repair_fixed_rate']*100:.1f}%")
    print(sep)
    print(f"  Post-repair valid JSON rate : {m['post_repair_valid']:2d} / {m['total']}  = {m['post_repair_valid_rate']*100:.1f}%")
    print(f"  Improvement                 : +{m['post_repair_valid'] - m['raw_valid']} examples  +{(m['post_repair_valid_rate'] - m['raw_valid_rate'])*100:.1f}pp")
    print(sep)
    print(f"  Avg LLM calls per example   : {m['avg_attempts']:.2f}")
    print(f"  % examples repair helped    : {m['pct_needed_repair']:.1f}%")
    print(f"  % examples repair failed    : {m['pct_repair_failed']:.1f}%")
    print(f"{'=' * 50}\n")
