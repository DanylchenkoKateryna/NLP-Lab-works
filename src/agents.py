"""
agents.py — TriagerAgent and ExtractorAgent for Lab 13 multi-agent crew.

TriagerAgent : reads input, selects extraction route, does NOT extract.
ExtractorAgent: performs structured extraction using tools from tools.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field

try:
    from tools import extract_entities, classify_category
except ImportError:
    from src.tools import extract_entities, classify_category


# ── Shared keyword vocabularies ───────────────────────────────────────────────

_ELECTRONICS_KW: tuple[str, ...] = (
    "transistor", "resistor", "capacitor", "diode", "circuit", "pcb",
    "oscilloscope", "multimeter", "microprocessor", "op-amp", "mosfet",
    "bjt", "fet", "zener", "rectifier", "regulator", "oscillator",
    "voltage", "current", "frequency", "schematic", "breadboard",
    "signal processing", "intel", "hewlett-packard", "electronics",
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

REQUIRED_FIELDS: list[str] = [
    "category", "persons", "organizations", "locations", "dates"
]

_ROUTE_MAP: dict[str, str] = {
    "electronics": "electronics_schema",
    "christian":   "religious_schema",
    "atheism":     "atheism_schema",
}

_TYPE_MAP: dict[str, str] = {
    "electronics": "electronics_classification",
    "christian":   "religious_classification",
    "atheism":     "atheism_classification",
}


# ── Triage Result ─────────────────────────────────────────────────────────────

@dataclass
class TriageResult:
    task_type: str
    route: str
    expected_fields: list
    difficulty: str
    notes: str

    def to_dict(self) -> dict:
        return {
            "task_type":       self.task_type,
            "route":           self.route,
            "expected_fields": self.expected_fields,
            "difficulty":      self.difficulty,
            "notes":           self.notes,
        }


# ── Triager ───────────────────────────────────────────────────────────────────

class TriagerAgent:
    """
    Routes input to the appropriate extraction schema.

    Does NOT extract entities — only analyses keyword evidence and sets:
      task_type, route, expected_fields, difficulty, notes.
    """

    def triage(self, text: str, task_id: str) -> TriageResult:
        if not text or not text.strip():
            return TriageResult(
                task_type="empty_input",
                route="unknown",
                expected_fields=["category"],
                difficulty="trivial",
                notes="Empty or blank input — cannot route",
            )

        lo = text.lower()
        scores = {
            "electronics": sum(1 for kw in _ELECTRONICS_KW if kw in lo),
            "christian":   sum(1 for kw in _CHRISTIAN_KW   if kw in lo),
            "atheism":     sum(1 for kw in _ATHEISM_KW      if kw in lo),
        }
        total = sum(scores.values())
        vals  = sorted(scores.values(), reverse=True)
        top   = max(scores, key=scores.get)
        is_tie   = (vals[0] == vals[1] and vals[1] > 0)
        is_empty = (total == 0)

        if is_empty:
            difficulty = "hard"
            route      = "unknown_schema"
            task_type  = "unknown_classification"
        elif is_tie:
            difficulty = "hard"
            route      = "mixed_schema"
            task_type  = "ambiguous_classification"
        elif vals[0] >= 4 and vals[1] == 0:
            difficulty = "easy"
            route      = _ROUTE_MAP[top]
            task_type  = _TYPE_MAP[top]
        elif vals[0] >= 2:
            difficulty = "medium"
            route      = _ROUTE_MAP[top]
            task_type  = _TYPE_MAP[top]
        else:
            difficulty = "hard"
            route      = _ROUTE_MAP.get(top, "unknown_schema")
            task_type  = _TYPE_MAP.get(top, "unknown_classification")

        notes_parts = [f"{cat}={cnt}" for cat, cnt in scores.items() if cnt > 0]
        if is_tie:
            notes_parts.append("tie → ambiguous routing")
        if is_empty:
            notes_parts.append("no keyword signal")
        if text and len(text.split()) < 8:
            notes_parts.append("very short text")

        return TriageResult(
            task_type=task_type,
            route=route,
            expected_fields=REQUIRED_FIELDS,
            difficulty=difficulty,
            notes="; ".join(notes_parts) if notes_parts else "no signal",
        )


# ── Extractor ─────────────────────────────────────────────────────────────────

class ExtractorAgent:
    """
    Extracts structured JSON using tools.py.
    Accepts an optional pre_extracted dict for simulation / test injection.
    """

    def extract(
        self,
        text: str,
        triage: TriageResult,
        task_id: str,
        pre_extracted: dict | None = None,
    ) -> dict:
        if pre_extracted is not None:
            return dict(pre_extracted)

        if not text or not text.strip():
            return {
                "category":        None,
                "persons":         [],
                "organizations":   [],
                "locations":       [],
                "dates":           [],
                "confidence_note": "empty input — no extraction possible",
                "_extraction_failed": True,
            }

        try:
            entities = extract_entities(text)
        except (ValueError, TypeError):
            entities = {
                "persons": [], "organizations": [], "locations": [],
                "dates": [], "raw_count": 0,
            }

        try:
            clf = classify_category(text)
        except (ValueError, TypeError):
            clf = {
                "category": "unknown", "confidence": 0.0,
                "is_ambiguous": False, "scores": {},
            }

        note_parts = []
        if clf["is_ambiguous"]:
            note_parts.append("ambiguous category")
        elif clf["confidence"] >= 0.8:
            note_parts.append(f"high confidence ({clf['confidence']:.0%})")
        elif clf["confidence"] >= 0.5:
            note_parts.append(f"medium confidence ({clf['confidence']:.0%})")
        else:
            note_parts.append(f"low confidence ({clf['confidence']:.0%})")

        if entities["raw_count"] == 0:
            note_parts.append("no entities found")
        else:
            note_parts.append(f"{entities['raw_count']} entities extracted")

        if triage.difficulty == "hard":
            note_parts.append("hard case per triager")

        return {
            "category":        clf["category"],
            "persons":         entities["persons"],
            "organizations":   entities["organizations"],
            "locations":       entities["locations"],
            "dates":           entities["dates"],
            "confidence_note": "; ".join(note_parts),
        }
