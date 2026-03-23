# IE Policy — Lab 4: Rule-Based Information Extraction

**Corpus:** 20 Newsgroups — `alt.atheism` / `sci.electronics` / `soc.religion.christian`
**Approach:** Precision-first regex + dictionary rules (no LLM/ML)
**Module:** `src/ie_rules.py`

---

## Field Type 1: DATE

### Definition
A calendar date explicitly mentioned in the text, expressed with a month name (spelled out or abbreviated), with or without a day and year component. Year-only and ISO-format dates are also included.

### Output format (normalization)
| Input | Normalized value |
|---|---|
| "January 3, 1993" | `1993-01-03` |
| "16 May 1993" | `1993-05-16` |
| "Jan 3" (no year) | `None-01-03` → stored as `month=1, day=3, year=None` |
| "1993-04-15" | `1993-04-15` |
| "4/15/93" | `1993-04-15` |

Each extracted entity includes: `value`, `year`, `month`, `day`, `method`.

### What is NOT a DATE
- Bare 4-digit numbers without month context: `"2000 years ago"` → NOT a DATE
- Version numbers: `"2.0"`, `"v1.3"` → NOT a DATE
- Time-only expressions: `"15:34"` → NOT a DATE
- Ordinal numbers without months: `"the 3rd"` → NOT a DATE
- Year ranges in citations: `"(Smith, 1985)"` → NOT a DATE (CITATION type)

### 5 edge cases from this corpus
1. `"valid until 16 may 1993"` — day-month-year in lowercase; must normalise month case
2. `"Scientific American's September 1992 issue"` — month + year without day
3. `"Skarda, 1985; Freeman 1987"` — years inside citations; should NOT extract as DATE (citation context)
4. `"the 1960's"` — decade reference; year 1960 extracted but decade marker ignored
5. `"circa 1964"` — approximate year; extracted as year-only DATE

---

## Field Type 2: ELEC_QTY

### Definition
A numerical measurement followed immediately (with optional whitespace) by an electrical or physical engineering unit. The number must precede the unit with no intervening words. Valid unit categories: frequency (Hz/kHz/MHz/GHz), voltage (V/mV/kV), current (A/mA/µA/nA), resistance (Ω/ohm/kΩ), power (W/mW/kW), capacitance (F/µF/nF/pF), inductance (H/mH/µH), signal level (dB/dBm), data rate (bps/kbps/Mbps), and rotational speed (rpm).

### Output format (normalization)
```json
{
  "numeric": 100.0,
  "unit_canonical": "MHz",
  "unit_type": "frequency"
}
```

### What is NOT an ELEC_QTY
- Part numbers with trailing letter: `"1615A"` (Hewlett-Packard logic analyser model) → NOT a qty (letter immediately precedes)
- Pure percentages: `"100%"` → NOT an ELEC_QTY
- `"500Ms/s"` (mega-samples per second) — NOT in unit dictionary; stored as unknown if matched
- Temperatures in non-electronics context: `"98°F body temperature"` → reject by context (no electronics surrounding)
- Counts/quantities without units: `"32 pins"` → NOT an ELEC_QTY

### 5 edge cases from this corpus
1. `"32kHz crystal"` — no space between number and unit; regex must allow zero whitespace
2. `"150uA"` — SI prefix `u` (ASCII) used instead of `µ` (Unicode); must normalise both
3. `"0.1uF cap"` — leading zero before decimal: `.1uF` → parse as `0.1 µF`
4. `"+14 dB line level"` — signed number; `+` sign before value must not break match
5. `"150-200\nohms"` — range expression; each bound extracted separately

---

## Field Type 3: SCRIPTURE_REF

### Definition
A reference to a Bible book or the Quran, followed by a chapter number and verse number(s), separated by a colon (`:`) or period (`.`). Verse ranges (e.g., `5:3-12`) are allowed. Books may be abbreviated (e.g., `Ps`, `Matt`, `Rev`) or numbered (e.g., `2 Peter`, `1 Cor`, `II Thess`). Roman numeral book prefixes (`I`, `II`, `III`) are normalised to arabic.

### Output format (normalization)
```json
{
  "book": "Matthew",
  "chapter": 25,
  "verse_start": 31,
  "verse_end": 46
}
```

### What is NOT a SCRIPTURE_REF
- Person names that match book names: `"John Smith"`, `"Mark Twain"` → NOT a ref (no chapter:verse)
- `"Acts of the Apostles"` without verse → NOT a ref
- `"The Book of Job"` without chapter:verse → NOT a ref
- Academic citation like `"(Romans 1, JRE 14/1)"` — the `(Romans 1,` part alone without verse → NOT a ref

### 5 edge cases from this corpus
1. `"Luke 22.20"` — period `.` used as chapter-verse separator instead of `:`
2. `"1 Corinthians 11.26"` — numbered book + period separator
3. `"2 Thessalonians 1:6-10"` — verse range with hyphen
4. `"Ex 33:19"` — highly abbreviated book name (only 2 chars)
5. `"Psalm 9:17"` — singular vs plural "Psalms" — both forms must be accepted

---

## Precision-first strategy

Rules are **conservative by design**:
- A match is only emitted when both the pattern AND the structural context confirm the field type.
- Ambiguous cases (e.g., `"John 3"` — could be person or scripture) are suppressed unless a colon/period separator is present.
- Part-number false positives for ELEC_QTY are blocked by checking whether the matched text is immediately preceded by a letter.
