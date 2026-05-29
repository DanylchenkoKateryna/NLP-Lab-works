"""
validator.py — JSON parse + schema validation for LLM extraction outputs.

Two-step validation
-------------------
Step 1: json.loads() — parse check
Step 2: jsonschema.validate() — schema check

Error types reported
--------------------
- parse_error     : raw output is not valid JSON
- schema_violation: JSON parsed but violates the schema
  sub-types: missing_required_field | wrong_type | enum_violation | extra_field
"""

from __future__ import annotations
import json
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

try:
    from json_schema import get_schema
except ImportError:
    from src.json_schema import get_schema


# ── Result dataclass ──────────────────────────────────────────────────────────

class ValidationResult:
    """Holds the outcome of a single validation attempt."""

    def __init__(
        self,
        raw: str,
        parse_ok: bool,
        schema_ok: bool,
        parsed: dict | None = None,
        parse_error: str | None = None,
        schema_errors: list[str] | None = None,
    ):
        self.raw          = raw
        self.parse_ok     = parse_ok
        self.schema_ok    = schema_ok
        self.parsed       = parsed
        self.parse_error  = parse_error
        self.schema_errors = schema_errors or []

    @property
    def valid(self) -> bool:
        return self.parse_ok and self.schema_ok

    def error_type(self) -> str | None:
        if not self.parse_ok:
            return "parse_error"
        if not self.schema_ok:
            return "schema_violation"
        return None

    def first_schema_error(self) -> str | None:
        return self.schema_errors[0] if self.schema_errors else None

    def short_error(self) -> str:
        if self.valid:
            return "OK"
        if not self.parse_ok:
            msg = self.parse_error or ""
            if "```" in self.raw:
                return "parse_error: code fence wrapping"
            if self.raw.strip() and self.raw.strip()[0] != "{":
                return "parse_error: not JSON at all"
            return f"parse_error: trailing text / malformed ({msg[:60]})"
        return f"schema_violation: {self.first_schema_error() or '?'}"

    def __repr__(self) -> str:
        if self.valid:
            return "ValidationResult(VALID)"
        return f"ValidationResult(INVALID: {self.short_error()})"


# ── Core functions ────────────────────────────────────────────────────────────

def validate_output(raw: str) -> ValidationResult:
    """
    Validate a single LLM output string.

    Returns a ValidationResult describing parse status and schema status.
    """
    schema = get_schema()

    # Step 1 — parse
    try:
        parsed = json.loads(raw)
        parse_ok    = True
        parse_error = None
    except json.JSONDecodeError as e:
        return ValidationResult(
            raw=raw, parse_ok=False, schema_ok=False,
            parsed=None, parse_error=str(e), schema_errors=[],
        )

    # Step 2 — schema
    errors: list[str] = []
    try:
        validate(instance=parsed, schema=schema)
        schema_ok = True
    except ValidationError:
        schema_ok = False
        validator = Draft7Validator(schema)
        errors = [err.message for err in validator.iter_errors(parsed)]

    return ValidationResult(
        raw=raw, parse_ok=True, schema_ok=schema_ok,
        parsed=parsed, parse_error=None, schema_errors=errors,
    )


def validate_batch(raws: list[str]) -> list[ValidationResult]:
    """Validate a list of raw LLM outputs."""
    return [validate_output(r) for r in raws]


def validation_summary(results: list[ValidationResult]) -> dict:
    """
    Compute aggregate validation statistics.

    Returns
    -------
    dict with keys:
      total, parse_ok, parse_fail, schema_ok, schema_fail, valid, invalid
    """
    n          = len(results)
    parse_ok   = sum(1 for r in results if r.parse_ok)
    schema_ok  = sum(1 for r in results if r.parse_ok and r.schema_ok)
    valid      = sum(1 for r in results if r.valid)
    return {
        "total":       n,
        "parse_ok":    parse_ok,
        "parse_fail":  n - parse_ok,
        "schema_ok":   schema_ok,
        "schema_fail": parse_ok - schema_ok,
        "valid":       valid,
        "invalid":     n - valid,
        "valid_rate":  round(valid / n, 4) if n else 0.0,
    }
