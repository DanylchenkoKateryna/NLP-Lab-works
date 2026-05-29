"""
embeddings_train.py — Word2Vec and FastText training utilities.

Trains gensim Word2Vec and FastText models on a tokenized corpus,
with consistent hyperparameters for fair comparison.
"""

import re
import logging
from typing import Optional

import numpy as np

logging.basicConfig(format="%(levelname)s : %(message)s", level=logging.WARNING)


# ── Default hyperparameters ──────────────────────────────────────────────────
DEFAULT_PARAMS = dict(
    vector_size=100,
    window=5,
    min_count=3,
    sg=1,           # Skip-Gram (better for rare/domain words than CBOW)
    workers=4,
    seed=42,
    epochs=10,
)

# FastText-specific: subword char n-grams
FASTTEXT_PARAMS = dict(
    **DEFAULT_PARAMS,
    min_n=3,        # min char n-gram length
    max_n=6,        # max char n-gram length
)


# ── Tokenization ─────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """
    Simple whitespace + punctuation tokenizer.
    Lowercases, strips non-alpha tokens shorter than 2 chars.
    """
    if not isinstance(text, str):
        return []
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z'-]{1,}", text)
    return tokens


def build_sentences(corpus: list[str]) -> list[list[str]]:
    """
    Convert list of document strings to list of token lists.
    Skips empty documents.
    """
    sentences = []
    for doc in corpus:
        toks = tokenize(doc)
        if toks:
            sentences.append(toks)
    return sentences


# ── Training ─────────────────────────────────────────────────────────────────

def train_word2vec(sentences: list[list[str]], **kwargs):
    """
    Train a Word2Vec Skip-Gram model.

    Parameters override DEFAULT_PARAMS.
    Returns trained gensim Word2Vec model.
    """
    from gensim.models import Word2Vec

    params = {**DEFAULT_PARAMS, **kwargs}
    model = Word2Vec(sentences=sentences, **params)
    return model


def train_fasttext(sentences: list[list[str]], **kwargs):
    """
    Train a FastText model with subword character n-grams.

    Parameters override FASTTEXT_PARAMS.
    Returns trained gensim FastText model.
    """
    from gensim.models import FastText

    params = {**FASTTEXT_PARAMS, **kwargs}
    model = FastText(sentences=sentences, **params)
    return model


# ── Corpus stats ─────────────────────────────────────────────────────────────

def corpus_stats(sentences: list[list[str]]) -> dict:
    """Return basic token and vocabulary statistics."""
    total_tokens = sum(len(s) for s in sentences)
    all_types = {tok for s in sentences for tok in s}
    lengths = [len(s) for s in sentences]
    return {
        "n_docs": len(sentences),
        "total_tokens": total_tokens,
        "vocab_size": len(all_types),
        "avg_doc_len": round(total_tokens / max(len(sentences), 1), 1),
        "min_doc_len": min(lengths) if lengths else 0,
        "max_doc_len": max(lengths) if lengths else 0,
    }


def print_corpus_stats(stats: dict, label: str = "Corpus") -> None:
    print(f"{label} statistics:")
    print(f"  Documents   : {stats['n_docs']:,}")
    print(f"  Total tokens: {stats['total_tokens']:,}")
    print(f"  Vocab size  : {stats['vocab_size']:,}")
    print(f"  Avg doc len : {stats['avg_doc_len']} tokens")
    print(f"  Min/Max len : {stats['min_doc_len']} / {stats['max_doc_len']}")
    print()
