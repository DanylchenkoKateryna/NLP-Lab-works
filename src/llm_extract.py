"""
llm_extract.py — LLM-based structured extraction for 20 Newsgroups.

Architecture
------------
BaseLLM           abstract base
MockLLM(BaseLLM)  pre-computed responses — no API key required.
                  Simulates realistic LLM behaviour including common
                  failure modes so the repair loop can be demonstrated.

In production replace MockLLM.call() with an actual LLM call
(e.g. google-generativeai, openai, huggingface hub inference).

Extraction task
---------------
From a 20 Newsgroups post fragment extract:
  category | persons | organizations | locations | dates |
  has_question | sentiment
"""

from __future__ import annotations

# ── Evaluation set ────────────────────────────────────────────────────────────

EVAL_TEXTS: list[str] = [
    # --- sci.electronics (9 texts) ---
    "I'm using a 2N2222 transistor and a 10k resistor to drive an LED. Can you help me choose the right current limiting resistor?",
    "Intel released its first microprocessor in November 1971. The MIT Media Lab has been doing great work on signal processing.",
    "Thu, 15 Apr 1993 09:45:12 -0500 -- anyone know a good oscilloscope brand? Hewlett-Packard makes reliable test equipment.",
    "The schematic shows a bridge rectifier followed by a voltage regulator. The PCB layout needs heat dissipation optimization.",
    "I need help with my op-amp circuit. The output voltage is oscillating at 100kHz. Can anyone explain why this happens?",
    "Hewlett-Packard makes excellent multimeters. I use the HP 34401A in my lab in San Jose for precision voltage measurements.",
    "The capacitor across the power supply should be at least 100uF. I am in Germany buying components from Farnell Electronics.",
    "FET transistors have better efficiency than BJT in switching applications at high frequencies. The MOSFET is preferred.",
    "Wed, 14 Apr 1993 20:11:04 -0400 -- posted from Cleveland State University. Zener diodes clamp voltage effectively.",
    # --- soc.religion.christian (6 texts) ---
    "Jesus Christ is the Son of God according to Christian belief. Paul wrote to the Corinthians about love and faith.",
    "The Virgin Mary is venerated in the Catholic Church. Pope John Paul II visited Poland in June 1979.",
    "According to the Bible, John the Baptist prepared the way for Jesus. The Holy Spirit descended on the apostles at Pentecost.",
    "The Council of Nicaea in 325 AD established the doctrine of the Trinity. Mother Teresa worked in Calcutta.",
    "Saint Peter was the first bishop of Rome. The Vatican is the seat of the Catholic Church in Italy.",
    "Fri, 23 Apr 1993 14:22:01 GMT -- the resurrection of Jesus Christ is the central claim of Christianity.",
    # --- alt.atheism (5 texts) ---
    "Richard Dawkins wrote The God Delusion in 2006. David Hume was an 18th-century Scottish philosopher and skeptic.",
    "The American Atheists organization was founded in 1963. Robert Ingersoll was a famous 19th-century agnostic.",
    "Carl Sagan\'s Cosmos series changed how millions think about science. NASA\'s Voyager mission explored the solar system.",
    "Bertrand Russell wrote Why I Am Not a Christian in 1927. His arguments against theism remain influential today.",
    "The University of California at Berkeley has a strong philosophy department. Susan Haack is a noted pragmatist philosopher.",
]

# Gold annotations for qualitative evaluation
GOLD_SET: list[dict] = [
    {"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": True, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": ["Intel", "MIT Media Lab"], "locations": [], "dates": ["November 1971"], "has_question": False, "sentiment": "positive"},
    {"category": "sci.electronics", "persons": [], "organizations": ["Hewlett-Packard"], "locations": [], "dates": ["Thu, 15 Apr 1993 09:45:12 -0500"], "has_question": True, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": False, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": True, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": ["Hewlett-Packard"], "locations": ["San Jose"], "dates": [], "has_question": False, "sentiment": "positive"},
    {"category": "sci.electronics", "persons": [], "organizations": ["Farnell Electronics"], "locations": ["Germany"], "dates": [], "has_question": False, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": False, "sentiment": "neutral"},
    {"category": "sci.electronics", "persons": [], "organizations": ["Cleveland State University"], "locations": [], "dates": ["Wed, 14 Apr 1993 20:11:04 -0400"], "has_question": False, "sentiment": "neutral"},
    {"category": "soc.religion.christian", "persons": ["Jesus Christ", "Paul"], "organizations": [], "locations": [], "dates": [], "has_question": False, "sentiment": "positive"},
    {"category": "soc.religion.christian", "persons": ["Virgin Mary", "Pope John Paul II"], "organizations": ["Catholic Church"], "locations": ["Poland"], "dates": ["June 1979"], "has_question": False, "sentiment": "neutral"},
    {"category": "soc.religion.christian", "persons": ["John the Baptist", "Jesus"], "organizations": [], "locations": [], "dates": [], "has_question": False, "sentiment": "neutral"},
    {"category": "soc.religion.christian", "persons": ["Mother Teresa"], "organizations": [], "locations": ["Calcutta"], "dates": ["325 AD"], "has_question": False, "sentiment": "neutral"},
    {"category": "soc.religion.christian", "persons": ["Saint Peter"], "organizations": ["Catholic Church"], "locations": ["Rome"], "dates": [], "has_question": False, "sentiment": "neutral"},
    {"category": "soc.religion.christian", "persons": ["Jesus Christ"], "organizations": [], "locations": [], "dates": ["Fri, 23 Apr 1993 14:22:01 GMT"], "has_question": False, "sentiment": "neutral"},
    {"category": "alt.atheism", "persons": ["Richard Dawkins", "David Hume"], "organizations": [], "locations": [], "dates": ["2006"], "has_question": False, "sentiment": "neutral"},
    {"category": "alt.atheism", "persons": ["Robert Ingersoll"], "organizations": ["American Atheists"], "locations": [], "dates": ["1963"], "has_question": False, "sentiment": "neutral"},
    {"category": "alt.atheism", "persons": ["Carl Sagan"], "organizations": ["NASA"], "locations": [], "dates": [], "has_question": False, "sentiment": "positive"},
    {"category": "alt.atheism", "persons": ["Bertrand Russell"], "organizations": [], "locations": [], "dates": ["1927"], "has_question": False, "sentiment": "neutral"},
    {"category": "alt.atheism", "persons": ["Susan Haack"], "organizations": ["University of California at Berkeley"], "locations": [], "dates": [], "has_question": False, "sentiment": "neutral"},
]

# Pre-computed MockLLM responses (raw attempt)
_RAW_RESPONSES: list[str] = [
    # 0 valid
    '{"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": true, "sentiment": "neutral"}',
    # 1 valid
    '{"category": "sci.electronics", "persons": [], "organizations": ["Intel", "MIT Media Lab"], "locations": [], "dates": ["November 1971"], "has_question": false, "sentiment": "positive"}',
    # 2 valid
    '{"category": "sci.electronics", "persons": [], "organizations": ["Hewlett-Packard"], "locations": [], "dates": ["Thu, 15 Apr 1993 09:45:12 -0500"], "has_question": true, "sentiment": "neutral"}',
    # 3 BROKEN: code fence
    '```json\n{"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": false, "sentiment": "neutral"}\n```',
    # 4 valid
    '{"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": true, "sentiment": "neutral"}',
    # 5 valid
    '{"category": "sci.electronics", "persons": [], "organizations": ["Hewlett-Packard"], "locations": ["San Jose"], "dates": [], "has_question": false, "sentiment": "positive"}',
    # 6 BROKEN: trailing text
    '{"category": "sci.electronics", "persons": [], "organizations": ["Farnell Electronics"], "locations": ["Germany"], "dates": [], "has_question": false, "sentiment": "neutral"}\n\nNote: The text mentions a capacitor specification (100uF) and a location (Germany). The organization Farnell Electronics is explicitly mentioned as the supplier.',
    # 7 valid
    '{"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": false, "sentiment": "neutral"}',
    # 8 BROKEN: missing required field "sentiment"
    '{"category": "sci.electronics", "persons": [], "organizations": ["Cleveland State University"], "locations": [], "dates": ["Wed, 14 Apr 1993 20:11:04 -0400"], "has_question": false}',
    # 9 valid
    '{"category": "soc.religion.christian", "persons": ["Jesus Christ", "Paul"], "organizations": [], "locations": [], "dates": [], "has_question": false, "sentiment": "positive"}',
    # 10 valid
    '{"category": "soc.religion.christian", "persons": ["Virgin Mary", "Pope John Paul II"], "organizations": ["Catholic Church"], "locations": ["Poland"], "dates": ["June 1979"], "has_question": false, "sentiment": "neutral"}',
    # 11 valid
    '{"category": "soc.religion.christian", "persons": ["John the Baptist", "Jesus"], "organizations": [], "locations": [], "dates": ["Pentecost"], "has_question": false, "sentiment": "neutral"}',
    # 12 BROKEN: wrong type has_question="false" (string not boolean)
    '{"category": "soc.religion.christian", "persons": ["Mother Teresa"], "organizations": [], "locations": ["Calcutta"], "dates": ["325 AD"], "has_question": "false", "sentiment": "neutral"}',
    # 13 valid
    '{"category": "soc.religion.christian", "persons": ["Saint Peter"], "organizations": ["Catholic Church"], "locations": ["Rome"], "dates": [], "has_question": false, "sentiment": "neutral"}',
    # 14 BROKEN: not JSON (permanent failure)
    "The extracted information from the text is as follows: The post category is soc.religion.christian. The main person mentioned is Jesus Christ. The date in the header is Fri, 23 Apr 1993 14:22:01 GMT. The post does not ask a question and its overall sentiment is neutral.",
    # 15 valid
    '{"category": "alt.atheism", "persons": ["Richard Dawkins", "David Hume"], "organizations": [], "locations": [], "dates": ["2006"], "has_question": false, "sentiment": "neutral"}',
    # 16 BROKEN: enum violation category="atheism"
    '{"category": "atheism", "persons": ["Robert Ingersoll"], "organizations": ["American Atheists"], "locations": [], "dates": ["1963"], "has_question": false, "sentiment": "neutral"}',
    # 17 valid
    '{"category": "alt.atheism", "persons": ["Carl Sagan"], "organizations": ["NASA"], "locations": [], "dates": [], "has_question": false, "sentiment": "positive"}',
    # 18 valid
    '{"category": "alt.atheism", "persons": ["Bertrand Russell"], "organizations": [], "locations": [], "dates": ["1927"], "has_question": false, "sentiment": "neutral"}',
    # 19 valid
    '{"category": "alt.atheism", "persons": ["Susan Haack"], "organizations": ["University of California at Berkeley"], "locations": [], "dates": [], "has_question": false, "sentiment": "neutral"}',
]

# Pre-computed repair responses (keyed by text index)
_REPAIR_RESPONSES: dict[int, str] = {
    3:  '{"category": "sci.electronics", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": false, "sentiment": "neutral"}',
    6:  '{"category": "sci.electronics", "persons": [], "organizations": ["Farnell Electronics"], "locations": ["Germany"], "dates": [], "has_question": false, "sentiment": "neutral"}',
    8:  '{"category": "sci.electronics", "persons": [], "organizations": ["Cleveland State University"], "locations": [], "dates": ["Wed, 14 Apr 1993 20:11:04 -0400"], "has_question": false, "sentiment": "neutral"}',
    12: '{"category": "soc.religion.christian", "persons": ["Mother Teresa"], "organizations": [], "locations": ["Calcutta"], "dates": ["325 AD"], "has_question": false, "sentiment": "neutral"}',
    14: "I apologize for the format error. Here is the information: category is soc.religion.christian, persons include Jesus Christ, the date is Fri 23 Apr 1993, has_question is false, sentiment is neutral. I am unable to return pure JSON for this input.",
    16: '{"category": "alt.atheism", "persons": ["Robert Ingersoll"], "organizations": ["American Atheists"], "locations": [], "dates": ["1963"], "has_question": false, "sentiment": "neutral"}',
}


# ── Prompt builders ───────────────────────────────────────────────────────────

EXTRACTION_PROMPT_TEMPLATE = """You are an information extraction system for 20 Newsgroups posts.
Extract structured information from the text below.

Return ONLY a valid JSON object with EXACTLY these fields:
  "category"      : one of ["sci.electronics", "soc.religion.christian", "alt.atheism"]
  "persons"       : array of person names mentioned (use [] if none)
  "organizations" : array of organization names (use [] if none)
  "locations"     : array of location / place names (use [] if none)
  "dates"         : array of date strings verbatim from text (use [] if none)
  "has_question"  : boolean true if text contains a question, false otherwise
  "sentiment"     : one of ["positive", "negative", "neutral", "mixed"]

Rules:
1. If a value is not present, use [] for arrays
2. Return ONLY the JSON object — no markdown, no code fences, no explanation
3. Do NOT add any text before or after the JSON

TEXT:
{text}

JSON:"""

REPAIR_PROMPT_TEMPLATE = """The previous extraction attempt returned an invalid output.

Original text:
{text}

Broken output:
{broken_output}

Validation error:
{error_message}

Please return a CORRECTED, valid JSON object that:
1. Fixes the specific validation error listed above
2. Contains ONLY these fields: category, persons, organizations, locations, dates, has_question, sentiment
3. Uses correct types: category and sentiment must be exact enum strings; has_question must be boolean (not string)
4. Has NO markdown, NO code fences, NO additional text

Return ONLY the corrected JSON:"""


def build_extraction_prompt(text: str) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(text=text)


def build_repair_prompt(text: str, broken_output: str, error_message: str) -> str:
    return REPAIR_PROMPT_TEMPLATE.format(
        text=text,
        broken_output=broken_output[:500],
        error_message=error_message[:300],
    )


# ── BaseLLM + MockLLM ─────────────────────────────────────────────────────────

class BaseLLM:
    """Abstract base class for LLM clients."""
    def call(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class MockLLM(BaseLLM):
    """
    Simulates an LLM with pre-computed responses.

    Parameters
    ----------
    noise_level : str
        "low"    — 70% raw valid (default, matches pre-computed data)
        "zero"   — always valid (for testing validator in isolation)

    In production, replace with a real LLM client:
        class GeminiLLM(BaseLLM):
            def call(self, prompt, **kwargs):
                return google.generativeai.generate(..., prompt)
    """

    def __init__(self, noise_level: str = "low"):
        self.noise_level = noise_level
        self._call_log: list[dict] = []

    def call(self, prompt: str, text_idx: int | None = None, attempt: int = 0) -> str:
        """
        Return a pre-computed response.

        Parameters
        ----------
        prompt     : the full prompt string (logged but not used for mock)
        text_idx   : index into EVAL_TEXTS (0-19)
        attempt    : 0 = raw extraction, 1+ = repair attempt
        """
        if text_idx is None or text_idx < 0 or text_idx >= len(_RAW_RESPONSES):
            return '{"category": "alt.atheism", "persons": [], "organizations": [], "locations": [], "dates": [], "has_question": false, "sentiment": "neutral"}'

        if self.noise_level == "zero":
            # Return gold-like valid JSON
            import json as _json
            gold = GOLD_SET[text_idx]
            return _json.dumps(gold)

        if attempt == 0:
            resp = _RAW_RESPONSES[text_idx]
        else:
            resp = _REPAIR_RESPONSES.get(text_idx, _RAW_RESPONSES[text_idx])

        self._call_log.append({"text_idx": text_idx, "attempt": attempt, "response_len": len(resp)})
        return resp

    def total_calls(self) -> int:
        return len(self._call_log)
