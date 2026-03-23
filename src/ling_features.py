"""
ling_features.py — Lemma/POS extraction via Stanza for the 20 Newsgroups NLP pipeline.

PII tokens (<URL>, <EMAIL>, <PHONE>) are protected before Stanza processing
and restored afterwards so they survive lemmatization unchanged.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import stanza
from tqdm import tqdm

_NLP_CACHE: Dict[str, stanza.Pipeline] = {}

_PII_PROTECT = [
    ("<URL>",   "urltoken"),
    ("<EMAIL>", "emailtoken"),
    ("<PHONE>", "phonetoken"),
]

_CONTENT_POS = {"NOUN", "ADJ", "VERB"}

def get_pipeline(lang: str = "en") -> stanza.Pipeline:
    """Initialise (or return cached) a Stanza pipeline for *lang*.

    The pipeline includes tokenization, POS tagging, and lemmatization.
    """
    if lang not in _NLP_CACHE:
        _NLP_CACHE[lang] = stanza.Pipeline(
            lang=lang,
            processors="tokenize,pos,lemma",
            use_gpu=False,
            verbose=False,
        )
    return _NLP_CACHE[lang]


def _protect_pii(text: str) -> str:
    """Replace angle-bracket PII tokens with plain ASCII placeholders."""
    for token, placeholder in _PII_PROTECT:
        text = text.replace(token, placeholder)
    return text


def _restore_pii(text: str) -> str:
    """Reverse _protect_pii — restore original PII tokens."""
    for token, placeholder in _PII_PROTECT:
        text = text.replace(placeholder, token)
    return text


def _truncate_words(text: str, max_words: int) -> str:
    """Keep only the first *max_words* whitespace-separated tokens."""
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return text


def extract_features(text: str, nlp: stanza.Pipeline) -> Dict[str, str]:
    """Extract lemma/POS features from *text* using *nlp*.

    Parameters
    ----------
    text:
        Raw input string (may contain <URL>/<EMAIL>/<PHONE> tokens).
    nlp:
        A Stanza Pipeline instance (from ``get_pipeline``).

    Returns
    -------
    dict with keys:
        ``lemma_text``
            Space-joined lowercased lemmas for every token.
        ``pos_seq``
            Space-joined UPOS tags for every token.
        ``content_lemma_text``
            Space-joined lowercased lemmas for NOUN / ADJ / VERB tokens only.
    """
    empty = {"lemma_text": "", "pos_seq": "", "content_lemma_text": ""}

    if not isinstance(text, str) or not text.strip():
        return empty

    # Protect PII tokens and truncate for performance
    protected = _protect_pii(text)
    protected = _truncate_words(protected, max_words=300)

    try:
        doc = nlp(protected)
    except Exception:
        return empty

    lemmas: List[str] = []
    pos_tags: List[str] = []
    content_lemmas: List[str] = []

    for sentence in doc.sentences:
        for word in sentence.words:
            lemma = (word.lemma or word.text).lower()
            upos = word.upos or "X"

            lemmas.append(lemma)
            pos_tags.append(upos)

            if upos in _CONTENT_POS:
                content_lemmas.append(lemma)

    lemma_text = _restore_pii(" ".join(lemmas))
    content_lemma_text = _restore_pii(" ".join(content_lemmas))
    pos_seq = " ".join(pos_tags)

    return {
        "lemma_text": lemma_text,
        "pos_seq": pos_seq,
        "content_lemma_text": content_lemma_text,
    }


def process_dataframe(
    df,
    text_col: str,
    nlp: stanza.Pipeline,
    max_words: int = 300,
) -> List[Dict[str, str]]:
    """Apply ``extract_features`` to every row in *df[text_col]*.

    Parameters
    ----------
    df:
        A pandas DataFrame.
    text_col:
        Name of the column containing raw text.
    nlp:
        Stanza Pipeline instance.
    max_words:
        Passed through for documentation; truncation is done inside
        ``extract_features``.

    Returns
    -------
    List of feature dicts (one per row), in the same order as *df*.
    """
    results: List[Dict[str, str]] = []
    texts = df[text_col].tolist()

    for text in tqdm(texts, desc="Extracting lemma/POS", unit="doc"):
        if not isinstance(text, str):
            text = ""
        results.append(extract_features(text, nlp))

    return results
