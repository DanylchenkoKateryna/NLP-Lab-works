"""
embeddings_eval.py — Nearest neighbor analysis and comparison utilities
for Word2Vec and FastText models.
"""

import pandas as pd
import numpy as np


# ── Neighbor lookup ──────────────────────────────────────────────────────────

def get_neighbors(model, word: str, topn: int = 10) -> list[tuple[str, float]]:
    """
    Return topn nearest neighbors for `word`.

    Works with both Word2Vec and FastText (FastText handles OOV via subwords).
    Returns list of (word, similarity) tuples, or [] if word not in vocab
    and model has no subword support.
    """
    try:
        return model.wv.most_similar(word, topn=topn)
    except KeyError:
        return []


def neighbors_to_str(neighbors: list[tuple[str, float]], n: int = 8) -> str:
    """Format neighbors as a compact string: 'word1(0.92), word2(0.89), ...'"""
    return ", ".join(f"{w}({s:.2f})" for w, s in neighbors[:n])


def neighbors_words(neighbors: list[tuple[str, float]], n: int = 8) -> list[str]:
    """Return just the word strings from a neighbors list."""
    return [w for w, _ in neighbors[:n]]


# ── Comparison table ─────────────────────────────────────────────────────────

def build_comparison_table(
    word_specs: list[dict],
    w2v_model,
    ft_model,
    topn: int = 8,
) -> pd.DataFrame:
    """
    Build a summary DataFrame comparing Word2Vec and FastText neighbors.

    word_specs: list of dicts with keys:
        word   : str
        type   : frequent | rare | domain | noisy | morph-variant
        useful : useful | partly | weak
        comment: str
    """
    rows = []
    for spec in word_specs:
        word = spec["word"]
        w2v_nb = get_neighbors(w2v_model, word, topn=topn)
        ft_nb  = get_neighbors(ft_model,  word, topn=topn)

        rows.append({
            "word":            word,
            "type":            spec.get("type", ""),
            "w2v_neighbors":   ", ".join(neighbors_words(w2v_nb, 5)),
            "ft_neighbors":    ", ".join(neighbors_words(ft_nb,  5)),
            "useful":          spec.get("useful", ""),
            "comment":         spec.get("comment", ""),
        })

    return pd.DataFrame(rows, columns=[
        "word", "type", "w2v_neighbors", "ft_neighbors", "useful", "comment"
    ])


# ── Case analysis ─────────────────────────────────────────────────────────────

def print_case(
    case_num: int,
    word: str,
    word_type: str,
    w2v_model,
    ft_model,
    verdict: str,
    reason: str,
    topn: int = 8,
) -> dict:
    """
    Print a single 'useful / not useful' case and return its data dict.

    verdict: 'useful' | 'not useful' | 'mixed'
    """
    w2v_nb = get_neighbors(w2v_model, word, topn=topn)
    ft_nb  = get_neighbors(ft_model,  word, topn=topn)

    print(f"{'='*60}")
    print(f"Case {case_num}: '{word}'  [{word_type}]")
    print(f"  Word2Vec : {neighbors_to_str(w2v_nb)}")
    print(f"  FastText : {neighbors_to_str(ft_nb)}")
    print(f"  Verdict  : {verdict.upper()}")
    print(f"  Why      : {reason}")
    print()

    return {
        "case": case_num,
        "word": word,
        "type": word_type,
        "w2v": neighbors_words(w2v_nb, 5),
        "ft":  neighbors_words(ft_nb,  5),
        "verdict": verdict,
        "reason":  reason,
    }


# ── Domain term analysis ──────────────────────────────────────────────────────

def analyze_domain_term(
    word: str,
    w2v_model,
    ft_model,
    topn: int = 10,
) -> dict:
    """
    Print and return domain term analysis for both models.
    """
    w2v_nb = get_neighbors(w2v_model, word, topn=topn)
    ft_nb  = get_neighbors(ft_model,  word, topn=topn)

    print(f"  '{word}'")
    print(f"    Word2Vec : {neighbors_to_str(w2v_nb)}")
    print(f"    FastText : {neighbors_to_str(ft_nb)}")

    return {"word": word, "w2v": w2v_nb, "ft": ft_nb}


# ── Vocabulary helpers ────────────────────────────────────────────────────────

def word_in_vocab(model, word: str) -> bool:
    """Check if word is in the model's explicit vocabulary."""
    return word in model.wv.key_to_index


def vocab_size(model) -> int:
    return len(model.wv.key_to_index)


def model_stats(model, label: str = "Model") -> None:
    """Print brief model stats."""
    print(f"{label}:")
    print(f"  Vocab size  : {vocab_size(model):,}")
    print(f"  Vector dim  : {model.wv.vector_size}")
    print()


# ── Similarity helpers ────────────────────────────────────────────────────────

def pairwise_similarity(model, words: list[str]) -> pd.DataFrame:
    """
    Return a symmetric DataFrame of cosine similarities between words.
    Skips words not in vocab (returns NaN).
    """
    sims = {}
    for w1 in words:
        row = {}
        for w2 in words:
            try:
                row[w2] = round(float(model.wv.similarity(w1, w2)), 3)
            except KeyError:
                row[w2] = float("nan")
        sims[w1] = row
    return pd.DataFrame(sims, index=words)


# ── audit_summary generator ───────────────────────────────────────────────────

def generate_audit_md(results: dict, output_path: str) -> None:
    """
    Write docs/audit_summary_lab9.md from a results dict.

    Expected keys: corpus_size, total_tokens, vocab_size,
    text_field, models, params, best_cases, weak_cases,
    domain_terms_ok, fasttext_wins, fasttext_tie, conclusion,
    worth_using.
    """
    lines = [
        "# Audit Summary — Lab 9: Word Embeddings (Word2Vec / FastText)\n",
        f"**Date:** 2026-05-29\n",
        "",
        "## 1. Corpus",
        f"- Documents  : **{results.get('corpus_size', 'N/A')}**",
        f"- Total tokens: {results.get('total_tokens', 'N/A'):,}" if isinstance(results.get('total_tokens'), int) else f"- Total tokens: {results.get('total_tokens', 'N/A')}",
        f"- Vocab size  : {results.get('vocab_size', 'N/A'):,}" if isinstance(results.get('vocab_size'), int) else f"- Vocab size  : {results.get('vocab_size', 'N/A')}",
        f"- Text field  : `{results.get('text_field', 'text_v2')}`",
        f"- Categories  : {results.get('categories', 'alt.atheism, sci.electronics, soc.religion.christian')}",
        "",
        "## 2. Models Trained",
    ]
    for m in results.get("models", []):
        lines.append(f"- {m}")

    lines += [
        "",
        "## 3. Hyperparameters",
        f"```",
    ]
    for k, v in results.get("params", {}).items():
        lines.append(f"{k} = {v}")
    lines += [
        "```",
        "",
        "## 4. Strongest Nearest-Neighbor Examples (2–3)",
    ]
    for ex in results.get("best_cases", []):
        lines.append(f"- **{ex['word']}** ({ex['type']}): {ex['neighbors']}")
        lines.append(f"  > {ex['why']}")

    lines += [
        "",
        "## 5. Weakest Examples (2–3)",
    ]
    for ex in results.get("weak_cases", []):
        lines.append(f"- **{ex['word']}** ({ex['type']}): {ex['neighbors']}")
        lines.append(f"  > Problem: {ex['why']}")

    lines += [
        "",
        "## 6. Domain Terms That Were Meaningful",
    ]
    for t in results.get("domain_terms_ok", []):
        lines.append(f"- {t}")

    lines += [
        "",
        "## 7. Where FastText Won",
        results.get("fasttext_wins", ""),
        "",
        "## 8. Where There Was No Clear Winner",
        results.get("fasttext_tie", ""),
        "",
        "## 9. Overall Conclusion",
        results.get("conclusion", ""),
        "",
        "## 10. Worth Using Embeddings Further?",
        results.get("worth_using", ""),
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved: {output_path}")
