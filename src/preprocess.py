import re
import html
import unicodedata

try:
    import nltk
    from nltk.tokenize import sent_tokenize
    for _res in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{_res}")
        except LookupError:
            nltk.download(_res, quiet=True)
    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False


# Protect existing PII tokens during clean_text so the pipeline is idempotent
_PII_TOKENS = [
    ("<URL>",   "__PII_URL__"),
    ("<EMAIL>", "__PII_EMAIL__"),
    ("<PHONE>", "__PII_PHONE__"),
]

_QUOTE_LINE = re.compile(r"^>+.*$", re.MULTILINE)
_IN_ARTICLE = re.compile(
    r"^In\s+(?:(?:article|message|reply)\s+)?<[^\s>]+>[^\n]*",
    re.IGNORECASE | re.MULTILINE,
)
_HEADER_LINE = re.compile(
    r"^(?:From|Subject|Date|Organization|Lines|NNTP-Posting-Host|"
    r"Message-ID|References|In-Reply-To|Newsgroups|Path|Xref|"
    r"Distribution|Keywords|Summary|Followup-To|Approved|Expires|"
    r"Reply-To|Sender|X-[\w-]+)\s*:.*$",
    re.MULTILINE | re.IGNORECASE,
)
_SIGNATURE = re.compile(r"\n--\s*\n.*", re.DOTALL)
# Matches lowercase-starting tag names only → <EMAIL>/<URL>/<PHONE> are safe
_HTML_TAG = re.compile(r"</?[a-z][a-zA-Z0-9]*(?:\s[^>]*)?\s*/?>")

_VERSION = re.compile(r"\b(\d+(?:\.\d+){2,})\b")
_DECIMAL = re.compile(r"\b(\d+\.\d+)\b")

_URL   = re.compile(r"https?://\S+|www\.\S+|ftp://\S+", re.IGNORECASE)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b")

_HOMOGLYPHS = {
    "\u0430": "a", "\u0435": "e", "\u0456": "i", "\u043e": "o",
    "\u0440": "p", "\u0441": "c", "\u0445": "x", "\u0443": "y",
    "\u0410": "A", "\u0415": "E", "\u0406": "I", "\u041e": "O",
    "\u0420": "P", "\u0421": "C", "\u0425": "X",
}


def clean_text(text: str) -> str:
    """Remove newsgroup artifacts and normalize whitespace."""
    if not isinstance(text, str) or not text:
        return ""

    for token, placeholder in _PII_TOKENS:
        text = text.replace(token, placeholder)

    text = html.unescape(text)
    text = _HTML_TAG.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # Strip each line before pattern removals so "^>" and "^From:" match correctly
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    text = _HEADER_LINE.sub("", text)
    text = _SIGNATURE.sub("", text)
    text = _QUOTE_LINE.sub("", text)
    text = _IN_ARTICLE.sub("", text)

    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    for token, placeholder in _PII_TOKENS:
        text = text.replace(placeholder, token)

    return text


def normalize_text(text: str) -> str:
    """Normalize Unicode characters: quotes, apostrophes, dashes, homoglyphs."""
    if not isinstance(text, str) or not text:
        return ""

    text = unicodedata.normalize("NFC", text)

    for ch in ("\u2019", "\u2018", "\u02bc", "\u02bb", "\u0060", "\u00b4"):
        text = text.replace(ch, "'")

    for ch in ("\u201c", "\u201d", "\u201e", "\u201f", "\u00ab", "\u00bb"):
        text = text.replace(ch, '"')

    text = text.replace("\u2014", "--")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2012", "-")

    text = text.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2009", " ")
    text = text.replace("\u2026", "...")

    for cyrillic, latin in _HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    text = re.sub(r" {2,}", " ", text)

    return text


def mask_pii(text: str) -> str:
    """Replace URLs, emails and phone numbers with placeholders."""
    if not isinstance(text, str) or not text:
        return ""

    # URL before email: some URLs contain @
    text = _URL.sub("<URL>", text)
    text = _EMAIL.sub("<EMAIL>", text)
    text = _PHONE.sub("<PHONE>", text)

    return text


def sentence_split(text: str) -> list:
    """Split text into sentences using NLTK Punkt (with version/decimal protection)."""
    if not isinstance(text, str) or not text.strip():
        return []

    _ver_store: list = []
    _dec_store: list = []

    def _protect_version(m: re.Match) -> str:
        _ver_store.append(m.group(0))
        return f"__VER{len(_ver_store) - 1}__"

    def _protect_decimal(m: re.Match) -> str:
        _dec_store.append(m.group(0))
        return f"__DEC{len(_dec_store) - 1}__"

    protected = _VERSION.sub(_protect_version, text)
    protected = _DECIMAL.sub(_protect_decimal, protected)

    if _NLTK_AVAILABLE:
        try:
            sentences = sent_tokenize(protected, language="english")
        except Exception:
            sentences = _fallback_split(protected)
    else:
        sentences = _fallback_split(protected)

    result = []
    for s in sentences:
        for i, v in enumerate(_ver_store):
            s = s.replace(f"__VER{i}__", v)
        for i, d in enumerate(_dec_store):
            s = s.replace(f"__DEC{i}__", d)
        s = s.strip()
        if s:
            result.append(s)

    return result


def preprocess(text: str) -> dict:
    """Full pipeline: clean → normalize → mask PII → sentence split."""
    cleaned    = clean_text(text)
    normalized = normalize_text(cleaned)
    masked     = mask_pii(normalized)
    sentences  = sentence_split(masked)

    return {
        "clean":          masked,
        "sentences":      sentences,
        "sentence_count": len(sentences),
        "char_length":    len(masked),
        "word_count":     len(masked.split()) if masked else 0,
    }


def count_replacements(text: str) -> dict:
    """Count PII tokens in raw text without modifying it (for audit stats)."""
    return {
        "urls":        len(_URL.findall(text)),
        "emails":      len(_EMAIL.findall(text)),
        "phones":      len(_PHONE.findall(text)),
        "quote_lines": len(_QUOTE_LINE.findall(text)),
    }


def _fallback_split(text: str) -> list:
    """Regex sentence splitter used when NLTK is unavailable."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", text)
    return [p.strip() for p in parts if p.strip()]
