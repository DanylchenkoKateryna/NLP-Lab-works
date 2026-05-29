"""
topic_utils.py — Corpus filtering and display utilities for topic modeling.
"""

import re
import pandas as pd
import numpy as np


# Extended stop-words specific to 20 Newsgroups discourse style
NEWSGROUP_EXTRA_STOPWORDS = {
    "subject", "from", "organization", "lines", "nntp", "posting",
    "host", "distribution", "newsgroup", "article", "writes", "wrote",
    "said", "say", "like", "just", "know", "think", "would", "could",
    "also", "one", "two", "get", "got", "use", "used", "make", "made",
    "way", "see", "much", "many", "may", "really", "even", "well",
    "want", "need", "good", "great", "right", "going", "come",
    "url", "email", "phone",                 # PII placeholders
    "newsgroup", "sci", "alt", "soc",        # category fragments
}

TEMPLATE_PATTERNS = [
    r"\bnewsgroup\s*:\s*\S+",
    r"\bdocument_id\s*:\s*\d+",
    r"<url>",
    r"<email>",
    r"<phone>",
]


def filter_corpus(
    df: pd.DataFrame,
    text_col: str = "text_v2",
    min_words: int = 15,
    max_words: int | None = None,
    label_col: str | None = "category",
) -> pd.DataFrame:
    """
    Remove empty, too-short, and optionally too-long documents.

    Returns filtered DataFrame and prints stats.
    """
    n_before = len(df)

    mask = df[text_col].notna() & (df[text_col].str.strip() != "")
    df = df[mask].copy()

    word_counts = df[text_col].str.split().str.len()
    df = df[word_counts >= min_words].copy()

    if max_words is not None:
        df = df[word_counts <= max_words].copy()

    n_after = len(df)
    print(f"Corpus filtering:")
    print(f"  Before : {n_before:,} documents")
    print(f"  After  : {n_after:,} documents  (removed {n_before - n_after})")
    if label_col and label_col in df.columns:
        print(f"  Label distribution after filter:")
        for label, cnt in df[label_col].value_counts().items():
            print(f"    {label}: {cnt:,} ({cnt/n_after*100:.1f}%)")
    print()
    return df


def strip_template_noise(text: str) -> str:
    """Remove newsgroup metadata footers and PII placeholders."""
    for pat in TEMPLATE_PATTERNS:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE)
    return text.strip()


def show_vectorizer_stats(vectorizer, matrix, name: str = "Vectorizer"):
    """Print vocabulary and matrix statistics."""
    vocab_size = len(vectorizer.vocabulary_)
    n_docs, n_feats = matrix.shape
    density = matrix.nnz / (n_docs * n_feats)
    print(f"{name} stats:")
    print(f"  Vocabulary size : {vocab_size:,}")
    print(f"  Matrix shape    : {n_docs:,} docs × {n_feats:,} features")
    print(f"  Matrix density  : {density:.4f}")
    print()


def format_topic_table(
    topics: list[list[str]],
    topic_names: list[str],
    model_label: str = "",
) -> pd.DataFrame:
    """Build a tidy DataFrame of topics for display."""
    rows = []
    for i, (words, name) in enumerate(zip(topics, topic_names)):
        rows.append({
            "model": model_label,
            "topic_id": i,
            "name": name,
            "top_words": ", ".join(words),
        })
    return pd.DataFrame(rows)


def dominant_topic_per_doc(doc_topic_matrix: np.ndarray) -> np.ndarray:
    """Return the index of the dominant topic for each document."""
    return np.argmax(np.abs(doc_topic_matrix), axis=1)


def topic_document_counts(
    doc_topic_matrix: np.ndarray,
    n_topics: int,
) -> pd.Series:
    """Count how many documents have each topic as dominant."""
    dominant = dominant_topic_per_doc(doc_topic_matrix)
    counts = pd.Series(dominant).value_counts().sort_index()
    counts.index.name = "topic_id"
    return counts


def assess_topic_quality(words: list[str], known_bad: set | None = None) -> str:
    """
    Heuristic quality label for a topic.

    Returns one of: 'good', 'generic', 'stop-word', 'noisy'
    """
    if known_bad is None:
        known_bad = NEWSGROUP_EXTRA_STOPWORDS

    bad_count = sum(1 for w in words if w in known_bad)
    ratio = bad_count / len(words)

    if ratio >= 0.5:
        return "stop-word / generic"
    if ratio >= 0.3:
        return "noisy"
    return "good"


def generate_audit_md(
    results: dict,
    output_path: str,
):
    """
    Write docs/audit_summary_lab8.md from a results dict.

    Expected keys: corpus_size, models_tested, k_values,
    best_topics, worst_topics, best_model, next_steps.
    """
    lines = [
        "# Audit Summary — Lab 8: Topic Modeling (LSA / LDA)\n",
        f"**Date:** 2026-05-28\n",
        "",
        "## 1. Corpus Size After Filtering",
        f"- Documents used: **{results.get('corpus_size', 'N/A')}**",
        f"- min_words filter: {results.get('min_words', 15)}",
        f"- Vectorizer min_df: {results.get('min_df', 5)}, max_df: {results.get('max_df', 0.90)}",
        "",
        "## 2. Models Tested",
    ]
    for m in results.get("models_tested", []):
        lines.append(f"- {m}")

    lines += [
        "",
        "## 3. k Values Tested",
    ]
    for k in results.get("k_values", []):
        lines.append(f"- k = {k}")

    lines += [
        "",
        "## 4. Best Topics (2–3 most useful)",
    ]
    for t in results.get("best_topics", []):
        lines.append(f"- **{t['name']}**: {t['words']}")
        lines.append(f"  > {t['why']}")

    lines += [
        "",
        "## 5. Worst Topics (2–3 problematic)",
    ]
    for t in results.get("worst_topics", []):
        lines.append(f"- **{t['name']}**: {t['words']}")
        lines.append(f"  > Problem: {t['problem']}")

    lines += [
        "",
        "## 6. What Caused Weak Topics",
        results.get("root_cause", ""),
        "",
        "## 7. Best Model for This Corpus",
        results.get("best_model", ""),
        "",
        "## 8. Next Steps",
    ]
    for step in results.get("next_steps", []):
        lines.append(f"- {step}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved: {output_path}")
