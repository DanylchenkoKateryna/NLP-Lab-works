"""
tools.py — Tool definitions for the NLP Research Post Analyzer agent.

Three tools, each a plain callable function:
  1. extract_entities(text)    — regex + keyword NER
  2. classify_category(text)   — keyword-score newsgroup classifier
  3. validate_extraction(data) — schema + consistency validator

Design principles (per ЛР12 requirements):
  - Clear name, typed input, structured dict output
  - Raises ValueError / TypeError for invalid inputs
  - Short docstring with param / return description
  - Predictable, deterministic behaviour (no LLM calls)
"""

from __future__ import annotations
import re


# ── Vocabulary ────────────────────────────────────────────────────────────────

KNOWN_PERSONS: list[str] = [
    "Richard Dawkins", "David Hume", "Bertrand Russell", "Carl Sagan",
    "Robert Ingersoll", "Susan Haack",
    "Jesus Christ", "Jesus of Nazareth", "Jesus",
    "John the Baptist", "Holy Spirit", "Virgin Mary", "Mother Mary",
    "Pope John Paul II", "Pope John Paul", "Mother Teresa",
    "Saint Peter", "Saint Paul", "Muhammad", "Allah", "Buddha", "Krishna",
]

KNOWN_ORGS: list[str] = [
    "Intel", "MIT Media Lab", "Hewlett-Packard",
    "Catholic Church", "American Atheists", "NASA",
    "Cleveland State University", "University of California at Berkeley",
    "Farnell Electronics", "Vatican", "Council of Nicaea",
]

KNOWN_LOCATIONS: list[str] = [
    "Poland", "Rome", "San Jose", "Germany", "Calcutta", "Italy",
    "Oxford", "Berkeley", "California", "Scotland", "Arabia", "Skopje",
]

# RFC-2822 + month-year + bare 4-digit year patterns
# Note: no \b word boundaries — they cause encoding issues in generator output;
# the (19|20)\d{2} prefix provides sufficient selectivity for 20th/21st-c years.
_DATE_RE = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+\d{1,2}\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}"
    r"\s+\d{2}:\d{2}(?::\d{2})?\s*(?:[+-]\d{4}|[A-Z]{2,4})?"
    r"|(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{4}"
    r"|\d{4}\s+AD"
    r"|(?:19|20)\d{2}",
    re.IGNORECASE,
)

_ELECTRONICS_KW: tuple[str, ...] = (
    "transistor", "resistor", "capacitor", "diode", "circuit", "pcb",
    "oscilloscope", "multimeter", "microprocessor", "op-amp", "mosfet",
    "bjt", "fet", "zener", "rectifier", "regulator", "oscillator",
    "voltage", "current", "frequency", "schematic", "breadboard",
    "signal processing", "intel", "hewlett-packard", "electronics",
    # NOTE: "electronic" intentionally omitted — it is a substring of "electronics"
    # and would double-count any text containing "electronics".
)

_CHRISTIAN_KW: tuple[str, ...] = (
    "jesus", "christ", "christian", "bible", "church", "catholic",
    "pope", "apostle", "holy spirit", "virgin mary", "baptism",
    "resurrection", "gospel", "faith", "trinity", "pentecost",
    "saint", "scripture", "theology", "bishop", "protestant",
)

_ATHEISM_KW: tuple[str, ...] = (
    "atheism", "atheist", "secular", "agnostic", "agnosticism",
    "skeptic", "theism", "dawkins", "david hume", "bertrand russell",
    "carl sagan", "evolution", "rational", "rationalism",
    "god delusion", "cosmos", "darwin", "philosophical", "philosopher",
)

VALID_CATEGORIES: frozenset[str] = frozenset({
    "sci.electronics", "soc.religion.christian", "alt.atheism",
    "unknown", "ambiguous",
})


# ── Helper ────────────────────────────────────────────────────────────────────

def _remove_subspans(names: list[str]) -> list[str]:
    """Drop names that are strict substrings of a longer name in the same list."""
    return [
        n for n in names
        if not any(
            n.lower() != o.lower() and n.lower() in o.lower()
            for o in names
        )
    ]


def _validate_text_input(text) -> None:
    if text is None:
        raise ValueError("Input text cannot be None")
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if not text.strip():
        raise ValueError("Input text cannot be empty")


# ── Tool 1 — Entity Extraction ────────────────────────────────────────────────

def extract_entities(text: str) -> dict:
    """
    Extract named entities from text using keyword lookup and regex patterns.

    Parameters
    ----------
    text : str  Non-empty input text.

    Returns
    -------
    dict
      persons       : list[str]  Person names found
      organizations : list[str]  Organization names found
      locations     : list[str]  Location/GPE names found
      dates         : list[str]  Date strings verbatim from text
      raw_count     : int        Total entity count

    Raises
    ------
    ValueError  If text is None or empty.
    TypeError   If text is not str.
    """
    _validate_text_input(text)
    lo = text.lower()

    persons       = _remove_subspans([p for p in KNOWN_PERSONS if p.lower() in lo])
    organizations = list(dict.fromkeys(o for o in KNOWN_ORGS if o.lower() in lo))
    locations     = list(dict.fromkeys(loc for loc in KNOWN_LOCATIONS if loc.lower() in lo))
    dates         = list(dict.fromkeys(m.group().strip() for m in _DATE_RE.finditer(text)))

    return {
        "persons":       persons,
        "organizations": organizations,
        "locations":     locations,
        "dates":         dates,
        "raw_count":     len(persons) + len(organizations) + len(locations) + len(dates),
    }


# ── Tool 2 — Category Classifier ─────────────────────────────────────────────

def classify_category(text: str) -> dict:
    """
    Classify text into one of three 20 Newsgroups categories.

    Uses keyword frequency scoring.  Returns "ambiguous" when top-2 scores
    are tied and > 0; returns "unknown" when all scores are 0.

    Parameters
    ----------
    text : str  Non-empty input text.

    Returns
    -------
    dict
      category      : str    Predicted category label
      confidence    : float  Top-category share of total keyword hits
      scores        : dict   Raw hit counts per category
      probabilities : dict   Normalised scores per category
      is_ambiguous  : bool   True when top-2 scores tie

    Raises
    ------
    ValueError  If text is None or empty.
    TypeError   If text is not str.
    """
    _validate_text_input(text)
    lo = text.lower()

    scores: dict[str, int] = {
        "sci.electronics":        sum(1 for kw in _ELECTRONICS_KW if kw in lo),
        "soc.religion.christian": sum(1 for kw in _CHRISTIAN_KW   if kw in lo),
        "alt.atheism":            sum(1 for kw in _ATHEISM_KW      if kw in lo),
    }
    total = sum(scores.values())

    if total == 0:
        return {
            "category":      "unknown",
            "confidence":    0.0,
            "scores":        scores,
            "probabilities": {k: 0.0 for k in scores},
            "is_ambiguous":  False,
        }

    top_cat  = max(scores, key=scores.get)
    top_val  = scores[top_cat]
    vals     = sorted(scores.values(), reverse=True)
    is_tie   = vals[0] == vals[1] and vals[1] > 0

    return {
        "category":      "ambiguous" if is_tie else top_cat,
        "confidence":    round(top_val / total, 3),
        "scores":        scores,
        "probabilities": {k: round(v / total, 3) for k, v in scores.items()},
        "is_ambiguous":  is_tie,
    }


# ── Tool 3 — Extraction Validator ────────────────────────────────────────────

def validate_extraction(data: dict) -> dict:
    """
    Validate structure and consistency of composed extraction data.

    Checks
    ------
    1. All required fields present
    2. Category is a known valid value; "ambiguous" is flagged as error
    3. Array fields are list instances
    4. Warns when all entity arrays are empty
    5. Warns when category is "unknown"

    Parameters
    ----------
    data : dict  Composed extraction dict to validate.

    Returns
    -------
    dict
      valid         : bool       No blocking errors
      errors        : list[str]  Blocking errors
      warnings      : list[str]  Non-blocking issues
      error_count   : int
      warning_count : int

    Raises
    ------
    TypeError  If data is not a dict.
    """
    if data is None or not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data).__name__}")

    REQUIRED = ("category", "persons", "organizations", "locations", "dates")
    errors:   list[str] = []
    warnings: list[str] = []

    for field in REQUIRED:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    if "category" in data:
        cat = data["category"]
        if cat == "ambiguous":
            errors.append(
                "Category is 'ambiguous' — cannot route to specific newsgroup"
            )
        elif cat not in VALID_CATEGORIES:
            errors.append(f"Invalid category value: '{cat}'")

    for arr in ("persons", "organizations", "locations", "dates"):
        if arr in data and not isinstance(data[arr], list):
            errors.append(
                f"Field '{arr}' must be list, got {type(data[arr]).__name__}"
            )

    # Completeness warning
    all_empty = all(
        isinstance(data.get(f), list) and not data.get(f)
        for f in ("persons", "organizations", "locations", "dates")
    )
    if all_empty and "category" in data:
        warnings.append("All entity lists are empty — extraction may be incomplete")

    if data.get("category") == "unknown":
        warnings.append("Category 'unknown' — classifier returned no keyword signal")

    return {
        "valid":         len(errors) == 0,
        "errors":        errors,
        "warnings":      warnings,
        "error_count":   len(errors),
        "warning_count": len(warnings),
    }
