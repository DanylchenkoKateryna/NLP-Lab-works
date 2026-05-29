"""
ner_rules.py — Hybrid rule-based layer for NER post-processing.

Three rules derived from observed baseline errors on the 20 Newsgroups corpus:

Rule 1 — ELECTRONICS_COMPONENT (regex + PhraseMatcher)
    Motivation: spaCy en_core_web_sm never tags electronics components
    (transistor, resistor, capacitor, diode …) as any entity type.
    These are important domain entities for sci.electronics documents.

Rule 2 — RELIGIOUS_FIGURE (PhraseMatcher → PERSON)
    Motivation: Compound religious names ("Jesus Christ", "Holy Spirit",
    "Paul the Apostle") are often split or missed by the baseline model.
    We add a phrase-level PERSON rule for the most common religious figures.

Rule 3 — USENET_DATE (regex → DATE)
    Motivation: RFC-2822 style dates in Usenet headers
    ("Mon, 15 Apr 1993 12:00:00 -0500") are NOT matched by spaCy as DATE
    because the full format includes timezone offsets.  A regex covers them.
"""

import re
import spacy
from spacy.tokens import Doc, Span
from spacy.language import Language
from spacy.matcher import PhraseMatcher


# ── Constants ────────────────────────────────────────────────────────────────

ELECTRONICS_TERMS = [
    "transistor", "transistors",
    "resistor", "resistors",
    "capacitor", "capacitors",
    "diode", "diodes",
    "op-amp", "op-amps",
    "mosfet", "mosfets",
    "oscilloscope",
    "multimeter",
    "voltmeter", "voltmeters",
    "ammeter",
    "breadboard",
    "schematic",
    "schematics",
    "waveform",
    "oscillator",
    "rectifier",
    "regulator",
    "zener",
    "bjt",
    "fet",
    "pcb",
]

RELIGIOUS_FIGURES = [
    "Jesus Christ",
    "Jesus of Nazareth",
    "Jesus",
    "Christ",
    "Holy Spirit",
    "Holy Ghost",
    "Virgin Mary",
    "Mother Mary",
    "John the Baptist",
    "Paul the Apostle",
    "Saint Paul",
    "Saint Peter",
    "Saint John",
    "Mother Teresa",
    "Pope John Paul II",
    "Pope John Paul",
    "Pope",
    "Muhammad",
    "Allah",
    "Buddha",
    "Krishna",
]

# RFC-2822 date: "Mon, 15 Apr 1993 12:00:00 +0000" or similar
USENET_DATE_REGEX = re.compile(
    r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+"
    r"\d{1,2}\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"\d{4}\s+"
    r"\d{2}:\d{2}(?::\d{2})?\s*"
    r"(?:[+-]\d{4}|[A-Z]{2,4})?",
    re.IGNORECASE,
)


# ── Rule 1: Electronics components ───────────────────────────────────────────

def build_electronics_matcher(nlp: Language) -> PhraseMatcher:
    """Build a PhraseMatcher for electronics component terms."""
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(term) for term in ELECTRONICS_TERMS]
    matcher.add("ELECTRONICS_COMPONENT", patterns)
    return matcher


def apply_electronics_rule(
    doc: Doc,
    matcher: PhraseMatcher,
) -> list[dict]:
    """
    Find electronics component mentions not already tagged by spaCy.

    Returns new entity dicts with label ELECTRONICS_COMPONENT.
    """
    matches = matcher(doc)
    existing_spans = {(e.start_char, e.end_char) for e in doc.ents}
    new_ents = []

    for match_id, start, end in matches:
        span = doc[start:end]
        # Skip if already covered by a spaCy entity
        if (span.start_char, span.end_char) not in existing_spans:
            new_ents.append({
                "text":       span.text,
                "label":      "ELECTRONICS_COMPONENT",
                "start_char": span.start_char,
                "end_char":   span.end_char,
            })

    return new_ents


# ── Rule 2: Religious figures ─────────────────────────────────────────────────

def build_religious_matcher(nlp: Language) -> PhraseMatcher:
    """Build a PhraseMatcher for religious figure names → PERSON."""
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(name) for name in RELIGIOUS_FIGURES]
    matcher.add("RELIGIOUS_FIGURE", patterns)
    return matcher


def apply_religious_rule(
    doc: Doc,
    matcher: PhraseMatcher,
) -> list[dict]:
    """
    Find religious figure names not tagged as PERSON by spaCy,
    or tagged with wrong type (e.g. ORG, NORP).

    Returns corrected/new entity dicts with label PERSON.
    """
    matches = matcher(doc)
    # Build index of existing ents by character range
    existing_by_range: dict[tuple[int, int], str] = {
        (e.start_char, e.end_char): e.label_ for e in doc.ents
    }
    new_ents = []

    for match_id, start, end in matches:
        span = doc[start:end]
        key = (span.start_char, span.end_char)

        existing_label = existing_by_range.get(key)
        if existing_label is None:
            # Missed entirely
            new_ents.append({
                "text":       span.text,
                "label":      "PERSON",
                "start_char": span.start_char,
                "end_char":   span.end_char,
                "rule_note":  "added by religious_figure rule",
            })
        elif existing_label not in ("PERSON",):
            # Wrong type — correct it
            new_ents.append({
                "text":       span.text,
                "label":      "PERSON",
                "start_char": span.start_char,
                "end_char":   span.end_char,
                "rule_note":  f"corrected from {existing_label} by religious_figure rule",
            })

    return new_ents


# ── Rule 3: Usenet RFC-2822 dates ─────────────────────────────────────────────

def apply_usenet_date_rule(doc: Doc, text: str) -> list[dict]:
    """
    Find RFC-2822 Usenet header dates not tagged as DATE by spaCy.

    Returns new entity dicts with label DATE.
    Hard-blocks only when an existing span extends OUTSIDE the proposed match
    (i.e. a wider span already exists).  Contained partial matches (e.g. spaCy
    tagging only the year "1993" inside a full RFC-2822 date) are superseded.
    """
    existing_spans = [(e.start_char, e.end_char) for e in doc.ents]
    new_ents = []

    for m in USENET_DATE_REGEX.finditer(text):
        start, end = m.start(), m.end()
        # Hard overlap: an existing span that overlaps AND is not fully
        # contained within our proposed span (meaning it extends outside).
        hard_overlap = any(
            not (end <= es or start >= ee)          # overlaps at all
            and not (es >= start and ee <= end)     # but is NOT a sub-span of ours
            for es, ee in existing_spans
        )
        if not hard_overlap:
            new_ents.append({
                "text":       m.group().strip(),
                "label":      "DATE",
                "start_char": start,
                "end_char":   end,
                "rule_note":  "added by usenet_date rule",
            })

    return new_ents


# ── Hybrid pipeline ───────────────────────────────────────────────────────────

class HybridNERPipeline:
    """
    Wraps spaCy baseline + 3 hybrid rules.

    Usage:
        pipeline = HybridNERPipeline(nlp)
        entities = pipeline.run(text)
    """

    def __init__(self, nlp: Language):
        self.nlp = nlp
        self.elec_matcher = build_electronics_matcher(nlp)
        self.relig_matcher = build_religious_matcher(nlp)

    def run_baseline(self, text: str) -> list[dict]:
        """Run spaCy NER only (no rules)."""
        doc = self.nlp(text)
        return [
            {"text": e.text, "label": e.label_,
             "start_char": e.start_char, "end_char": e.end_char}
            for e in doc.ents
        ]

    def run_hybrid(self, text: str) -> list[dict]:
        """Run spaCy NER + all 3 hybrid rules."""
        doc = self.nlp(text)
        base_ents = [
            {"text": e.text, "label": e.label_,
             "start_char": e.start_char, "end_char": e.end_char}
            for e in doc.ents
        ]

        r1 = apply_electronics_rule(doc, self.elec_matcher)
        r2 = apply_religious_rule(doc, self.relig_matcher)
        r3 = apply_usenet_date_rule(doc, text)

        all_ents = base_ents + r1 + r2 + r3

        # Resolve overlaps: greedy by span length (longest span wins).
        # This removes shorter spaCy spans that are superseded by wider rule spans,
        # and prevents duplicate sub-span false positives from the phrase matcher.
        sorted_by_len = sorted(
            all_ents,
            key=lambda x: (x["end_char"] - x["start_char"]),
            reverse=True,
        )
        kept: list[dict] = []
        for e in sorted_by_len:
            s, en = e["start_char"], e["end_char"]
            if not any(
                not (en <= k["start_char"] or s >= k["end_char"])
                for k in kept
            ):
                kept.append(e)

        return sorted(kept, key=lambda x: x["start_char"])

    def run_batch_baseline(self, texts: list[str]) -> list[list[dict]]:
        return [self.run_baseline(t) for t in texts]

    def run_batch_hybrid(self, texts: list[str]) -> list[list[dict]]:
        return [self.run_hybrid(t) for t in texts]
