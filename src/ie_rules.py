"""
ie_rules.py — Rule-based Information Extraction (Lab 4)

Field types:
  DATE          — dates with month names or ISO format
  ELEC_QTY      — electrical quantities (V, A, Hz, Ω, W, F, H, dB, …)
  SCRIPTURE_REF — Bible / Quran verse references (Book Chapter:Verse)

Each extracted entity dict has: field_type, raw, start_char, end_char, method, value.
"""

import re
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Dictionaries
# ---------------------------------------------------------------------------

MONTH_NAME_TO_NUM = {
    "january": 1, "jan": 1, "february": 2, "feb": 2,
    "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5,
    "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# lowercase unit → (canonical, unit_type)
ELEC_UNIT_MAP: Dict[str, tuple] = {
    "hz": ("Hz", "frequency"), "khz": ("kHz", "frequency"),
    "mhz": ("MHz", "frequency"), "ghz": ("GHz", "frequency"),
    "v": ("V", "voltage"), "mv": ("mV", "voltage"), "kv": ("kV", "voltage"),
    "uv": ("µV", "voltage"), "volt": ("V", "voltage"), "volts": ("V", "voltage"),
    "a": ("A", "current"), "ma": ("mA", "current"), "ua": ("µA", "current"),
    "na": ("nA", "current"), "amp": ("A", "current"), "amps": ("A", "current"),
    "ampere": ("A", "current"), "amperes": ("A", "current"),
    "milliamp": ("mA", "current"), "milliamps": ("mA", "current"),
    "ohm": ("Ω", "resistance"), "ohms": ("Ω", "resistance"),
    "kohm": ("kΩ", "resistance"), "kohms": ("kΩ", "resistance"),
    "mohm": ("MΩ", "resistance"), "mohms": ("MΩ", "resistance"),
    "w": ("W", "power"), "mw": ("mW", "power"), "kw": ("kW", "power"),
    "watt": ("W", "power"), "watts": ("W", "power"),
    "f": ("F", "capacitance"), "uf": ("µF", "capacitance"),
    "nf": ("nF", "capacitance"), "pf": ("pF", "capacitance"),
    "farad": ("F", "capacitance"), "farads": ("F", "capacitance"),
    "h": ("H", "inductance"), "mh": ("mH", "inductance"), "uh": ("µH", "inductance"),
    "henry": ("H", "inductance"), "henries": ("H", "inductance"),
    "db": ("dB", "level"), "dbm": ("dBm", "level"),
    "bps": ("bps", "data_rate"), "kbps": ("kbps", "data_rate"),
    "mbps": ("Mbps", "data_rate"), "gbps": ("Gbps", "data_rate"),
    "rpm": ("rpm", "speed"),
}

# All known Bible / Quran book aliases → canonical name
BIBLE_BOOK_ALIASES: Dict[str, str] = {}

_BIBLE_BOOKS_RAW = [
    ("Genesis",         ["gen", "genesis"]),
    ("Exodus",          ["ex", "exod", "exodus"]),
    ("Leviticus",       ["lev", "leviticus"]),
    ("Numbers",         ["num", "numbers"]),
    ("Deuteronomy",     ["deut", "deuteronomy"]),
    ("Joshua",          ["josh", "joshua"]),
    ("Judges",          ["judg", "judges"]),
    ("Ruth",            ["ruth"]),
    ("1 Samuel",        ["1 sam", "1sam", "1samuel", "i sam", "i samuel"]),
    ("2 Samuel",        ["2 sam", "2sam", "2samuel", "ii sam", "ii samuel"]),
    ("1 Kings",         ["1 kgs", "1kgs", "1 kings", "1kings", "i kings", "i kgs"]),
    ("2 Kings",         ["2 kgs", "2kgs", "2 kings", "2kings", "ii kings", "ii kgs"]),
    ("1 Chronicles",    ["1 chr", "1chr", "1chronicles", "i chr"]),
    ("2 Chronicles",    ["2 chr", "2chr", "2chronicles", "ii chr"]),
    ("Ezra",            ["ezra"]),
    ("Nehemiah",        ["neh", "nehemiah"]),
    ("Esther",          ["esth", "esther"]),
    ("Job",             ["job"]),
    ("Psalms",          ["ps", "psa", "psalm", "psalms"]),
    ("Proverbs",        ["prov", "proverbs"]),
    ("Ecclesiastes",    ["eccl", "ecclesiastes"]),
    ("Song of Solomon", ["song", "song of solomon", "sos"]),
    ("Isaiah",          ["isa", "isaiah"]),
    ("Jeremiah",        ["jer", "jeremiah"]),
    ("Lamentations",    ["lam", "lamentations"]),
    ("Ezekiel",         ["ezek", "ezekiel"]),
    ("Daniel",          ["dan", "daniel"]),
    ("Hosea",           ["hos", "hosea"]),
    ("Joel",            ["joel"]),
    ("Amos",            ["amos"]),
    ("Obadiah",         ["obad", "obadiah"]),
    ("Jonah",           ["jon", "jonah"]),
    ("Micah",           ["mic", "micah"]),
    ("Nahum",           ["nah", "nahum"]),
    ("Habakkuk",        ["hab", "habakkuk"]),
    ("Zephaniah",       ["zeph", "zephaniah"]),
    ("Haggai",          ["hag", "haggai"]),
    ("Zechariah",       ["zech", "zechariah"]),
    ("Malachi",         ["mal", "malachi"]),
    ("Matthew",         ["matt", "matthew"]),
    ("Mark",            ["mark"]),
    ("Luke",            ["luke"]),
    ("John",            ["john"]),
    ("Acts",            ["acts"]),
    ("Romans",          ["rom", "romans"]),
    ("1 Corinthians",   ["1 cor", "1cor", "1corinthians", "i cor"]),
    ("2 Corinthians",   ["2 cor", "2cor", "2corinthians", "ii cor"]),
    ("Galatians",       ["gal", "galatians"]),
    ("Ephesians",       ["eph", "ephesians"]),
    ("Philippians",     ["phil", "philippians"]),
    ("Colossians",      ["col", "colossians"]),
    ("1 Thessalonians", ["1 thess", "1thess", "1thessalonians", "i thess"]),
    ("2 Thessalonians", ["2 thess", "2thess", "2thessalonians", "ii thess"]),
    ("1 Timothy",       ["1 tim", "1tim", "1timothy", "i tim"]),
    ("2 Timothy",       ["2 tim", "2tim", "2timothy", "ii tim"]),
    ("Titus",           ["titus"]),
    ("Philemon",        ["phlm", "philem", "philemon"]),
    ("Hebrews",         ["heb", "hebrews"]),
    ("James",           ["jas", "james"]),
    ("1 Peter",         ["1 pet", "1pet", "1peter", "i pet"]),
    ("2 Peter",         ["2 pet", "2pet", "2peter", "ii pet"]),
    ("1 John",          ["1 john", "1john", "i john"]),
    ("2 John",          ["2 john", "2john", "ii john"]),
    ("3 John",          ["3 john", "3john", "iii john"]),
    ("Jude",            ["jude"]),
    ("Revelation",      ["rev", "revelation"]),
    ("Quran",           ["quran", "qur'an", "sura", "surah"]),
]

for canonical, aliases in _BIBLE_BOOKS_RAW:
    for alias in aliases:
        BIBLE_BOOK_ALIASES[alias.lower()] = canonical
    BIBLE_BOOK_ALIASES[canonical.lower()] = canonical


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

_MONTH_ALT = (
    r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
)
# "January 3, 1993" / "Jan 3rd"
_DATE_MDY = re.compile(
    r'\b(' + _MONTH_ALT + r')\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:[,\s]+(\d{4}))?\b', re.I)
# "16 May 1993"
_DATE_DMY = re.compile(
    r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + _MONTH_ALT + r')\.?(?:\s+(\d{4}))?\b', re.I)
# "September 1992" (no day)
_DATE_MY = re.compile(r'\b(' + _MONTH_ALT + r')\.?[,\s]+(\d{4})\b', re.I)
# ISO "1993-04-15"
_DATE_ISO = re.compile(r'\b((?:19|20)\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b')
# US slash "4/15/1993"
_DATE_US = re.compile(r'\b(\d{1,2})/(\d{1,2})/((?:19|20)?\d{2})\b')
# Year with context keyword: "circa 1964", "since 1993"
_DATE_YEAR_CTX = re.compile(
    r'(?:circa|since|in|around|after|before|by|from|until|as\s+of)\s+((?:19|20)\d{2})\b', re.I)

# Number + electrical unit (no leading dot/digit to avoid decimals and part numbers)
_ELEC_QTY = re.compile(
    r'(?<![.\d])(\d+(?:\.\d+)?)\s*'
    r'(MHz|GHz|kHz|Hz'
    r'|[mkMK]?V(?:olt(?:s)?)?(?!\w)'
    r'|[mkMK]?A(?:mp(?:ere)?s?)?(?!\w)'
    r'|[mkMK]?W(?:att(?:s)?)?(?!\w)'
    r'|[mkMK]?[Oo]hm(?:s)?(?!\w)'
    r'|[pnuµm]?F(?:arad(?:s)?)?(?!\w)'
    r'|[munµ]?H(?:enr(?:y|ies))?(?!\w)'
    r'|dBm?|[KMG]?bps|rpm)\b',
    re.I,
)
# µ-prefix (Unicode micro sign)
_ELEC_QTY_MU = re.compile(r'\b(\d+(?:\.\d+)?)\s*(µ[VAF])\b')

# Bible/Quran: full alias + chapter + separator + verse (+ optional range)
_sorted_aliases = sorted(BIBLE_BOOK_ALIASES.keys(), key=len, reverse=True)
_book_alt = '|'.join(re.escape(a) for a in _sorted_aliases)
_SCRIPTURE = re.compile(
    r'\b(' + _book_alt + r")'?\.?\s+(\d+)[.:\s](\d+)(?:\s*[-–]\s*(\d+))?",
    re.I,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_year(y_str: str | None) -> int | None:
    if y_str is None:
        return None
    y = int(y_str)
    if y < 100:
        y += 1900 if y >= 93 else 2000
    return y


def _make_entity(field_type, raw, start, end, method, **extra) -> Dict[str, Any]:
    e = {"field_type": field_type, "raw": raw, "start_char": start, "end_char": end, "method": method}
    e.update(extra)
    return e


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

def extract_dates(text: str) -> List[Dict]:
    """Extract DATE entities. Normalised value: YYYY-MM-DD / YYYY-MM / YYYY."""
    results = []
    seen: set = set()

    def _add(m, year, month, day, method):
        s, e = m.start(), m.end()
        if (s, e) in seen:
            return
        # Skip if this span is fully contained within an already-added span
        if any(ps <= s and e <= pe for ps, pe in seen):
            return
        seen.add((s, e))
        if month and day and year:
            value = f"{year:04d}-{month:02d}-{day:02d}"
        elif month and year:
            value = f"{year:04d}-{month:02d}"
        elif year:
            value = f"{year:04d}"
        else:
            value = m.group()
        results.append(_make_entity("DATE", m.group(), s, e, method,
                                    value=value, year=year, month=month, day=day))

    for m in _DATE_ISO.finditer(text):
        _add(m, int(m.group(1)), int(m.group(2)), int(m.group(3)), "regex_iso")

    for m in _DATE_MDY.finditer(text):
        mo = MONTH_NAME_TO_NUM.get(m.group(1).lower().rstrip("."))
        d, y = int(m.group(2)), _parse_year(m.group(3))
        if mo and 1 <= d <= 31:
            _add(m, y, mo, d, "regex_mdy")

    for m in _DATE_DMY.finditer(text):
        d = int(m.group(1))
        mo = MONTH_NAME_TO_NUM.get(m.group(2).lower().rstrip("."))
        y = _parse_year(m.group(3))
        if mo and 1 <= d <= 31:
            _add(m, y, mo, d, "regex_dmy")

    for m in _DATE_MY.finditer(text):
        mo = MONTH_NAME_TO_NUM.get(m.group(1).lower().rstrip("."))
        if mo:
            _add(m, int(m.group(2)), mo, None, "regex_my")

    for m in _DATE_YEAR_CTX.finditer(text):
        _add(m, int(m.group(1)), None, None, "regex_year_ctx")

    for m in _DATE_US.finditer(text):
        mo, d, y = int(m.group(1)), int(m.group(2)), _parse_year(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            _add(m, y, mo, d, "regex_us")

    results.sort(key=lambda x: x["start_char"])
    return results


def extract_elec_qty(text: str) -> List[Dict]:
    """Extract ELEC_QTY entities. Value: {numeric, unit_canonical, unit_type}."""
    results = []
    seen: set = set()

    def _add(m, num_str, unit_raw, method):
        s, e = m.start(), m.end()
        if (s, e) in seen:
            return
        if s > 0 and text[s - 1].isalpha():
            return
        # Reject part numbers: large integer fused with a single uppercase letter
        try:
            num_val = float(num_str)
        except ValueError:
            num_val = 0
        raw_unit = unit_raw.strip()
        if num_val >= 100 and len(raw_unit) == 1 and raw_unit.isupper():
            no_space = m.group(0).replace(num_str, "", 1).lstrip() == raw_unit
            if no_space:
                return
        seen.add((s, e))
        canonical, unit_type = ELEC_UNIT_MAP.get(raw_unit.lower(), (raw_unit, "unknown"))
        try:
            numeric = float(num_str)
        except ValueError:
            numeric = None
        results.append(_make_entity("ELEC_QTY", m.group(), s, e, method,
                                    value={"numeric": numeric, "unit_canonical": canonical,
                                           "unit_type": unit_type}))

    for m in _ELEC_QTY.finditer(text):
        _add(m, m.group(1), m.group(2), "regex_elec")
    for m in _ELEC_QTY_MU.finditer(text):
        _add(m, m.group(1), m.group(2), "regex_elec_mu")

    results.sort(key=lambda x: x["start_char"])
    return results


def extract_scripture_refs(text: str) -> List[Dict]:
    """Extract SCRIPTURE_REF entities. Value: {book, chapter, verse_start, verse_end}."""
    results = []
    seen: set = set()
    # Common English first names that also match book aliases — require explicit separator
    _AMBIGUOUS = {"john", "mark", "luke", "ruth", "joel", "amos", "daniel", "james"}

    for m in _SCRIPTURE.finditer(text):
        s, e = m.start(), m.end()
        if (s, e) in seen:
            continue
        seen.add((s, e))

        alias_raw = m.group(1).lower().strip().rstrip("'")
        chapter   = int(m.group(2))
        verse_s   = int(m.group(3))
        verse_e   = int(m.group(4)) if m.group(4) else None

        canonical = BIBLE_BOOK_ALIASES.get(alias_raw)
        if canonical is None:
            continue

        if alias_raw in _AMBIGUOUS:
            sep_pos = m.end(2)
            sep_char = text[sep_pos] if sep_pos < len(text) else " "
            if sep_char not in (":", "."):
                continue

        results.append(_make_entity("SCRIPTURE_REF", m.group(), s, e, "regex_scripture",
                                    value={"book": canonical, "chapter": chapter,
                                           "verse_start": verse_s, "verse_end": verse_e}))

    results.sort(key=lambda x: x["start_char"])
    return results


def extract_all(text: str) -> Dict[str, List[Dict]]:
    """Run all extractors. Returns {DATE: [...], ELEC_QTY: [...], SCRIPTURE_REF: [...]}."""
    return {
        "DATE":          extract_dates(text),
        "ELEC_QTY":      extract_elec_qty(text),
        "SCRIPTURE_REF": extract_scripture_refs(text),
    }
