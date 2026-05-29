"""
topic_modeling.py — LSA and LDA topic modeling utilities.

Builds TF-IDF + TruncatedSVD (LSA) and CountVectorizer + LDA pipelines,
extracts top words and top documents per topic.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation


def build_lsa_model(
    corpus: list[str],
    n_components: int = 8,
    min_df: int = 5,
    max_df: float = 0.90,
    ngram_range: tuple = (1, 1),
    random_state: int = 42,
):
    """
    Fit TF-IDF vectorizer + TruncatedSVD (LSA).

    Returns (svd_model, tfidf_matrix, vectorizer, doc_topic_matrix)
    """
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
        stop_words="english",
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    svd = TruncatedSVD(n_components=n_components, random_state=random_state)
    doc_topic_matrix = svd.fit_transform(tfidf_matrix)

    return svd, tfidf_matrix, vectorizer, doc_topic_matrix


def build_lda_model(
    corpus: list[str],
    n_components: int = 8,
    min_df: int = 5,
    max_df: float = 0.90,
    ngram_range: tuple = (1, 1),
    random_state: int = 42,
    max_iter: int = 20,
):
    """
    Fit CountVectorizer + LatentDirichletAllocation.

    Returns (lda_model, count_matrix, vectorizer, doc_topic_matrix)
    """
    vectorizer = CountVectorizer(
        analyzer="word",
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        stop_words="english",
    )
    count_matrix = vectorizer.fit_transform(corpus)

    lda = LatentDirichletAllocation(
        n_components=n_components,
        random_state=random_state,
        max_iter=max_iter,
        learning_method="online",
        doc_topic_prior=0.1,
        topic_word_prior=0.01,
    )
    doc_topic_matrix = lda.fit_transform(count_matrix)

    return lda, count_matrix, vectorizer, doc_topic_matrix


def get_top_words(model, vectorizer, n_words: int = 10) -> list[list[str]]:
    """
    Extract top-N words for each topic from a fitted model (LSA or LDA).

    For LSA (TruncatedSVD): uses absolute component values.
    For LDA: uses component_ probabilities directly.
    """
    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, component in enumerate(model.components_):
        if isinstance(model, TruncatedSVD):
            top_indices = np.argsort(np.abs(component))[::-1][:n_words]
        else:
            top_indices = np.argsort(component)[::-1][:n_words]
        top_words = [feature_names[i] for i in top_indices]
        topics.append(top_words)

    return topics


def get_top_documents(
    doc_topic_matrix: np.ndarray,
    docs: list[str],
    topic_idx: int,
    n_docs: int = 3,
    labels: list | None = None,
) -> pd.DataFrame:
    """
    Return the top-N documents with highest weight for a given topic.
    """
    weights = doc_topic_matrix[:, topic_idx]
    top_indices = np.argsort(np.abs(weights))[::-1][:n_docs]

    rows = []
    for rank, idx in enumerate(top_indices):
        row = {
            "rank": rank + 1,
            "doc_idx": idx,
            "weight": round(float(weights[idx]), 4),
            "text_snippet": docs[idx][:300].replace("\n", " "),
        }
        if labels is not None:
            row["label"] = labels[idx]
        rows.append(row)

    return pd.DataFrame(rows)


def print_topics(
    topics: list[list[str]],
    topic_names: list[str] | None = None,
    model_name: str = "Model",
    k: int | None = None,
):
    """Pretty-print topic top-words with optional human names."""
    header = f"{'='*60}\n{model_name}"
    if k:
        header += f" (k={k})"
    print(header)
    print("=" * 60)

    for i, words in enumerate(topics):
        name = topic_names[i] if topic_names else f"Topic {i}"
        print(f"  Topic {i:2d} [{name}]: {', '.join(words)}")
    print()


def explained_variance_lsa(svd_model) -> dict:
    """Return explained variance ratio per component and cumulative."""
    evr = svd_model.explained_variance_ratio_
    return {
        "per_component": evr.tolist(),
        "cumulative": np.cumsum(evr).tolist(),
        "total": float(evr.sum()),
    }


def topic_diversity(topics: list[list[str]]) -> float:
    """
    Proportion of unique words across all topics.
    High diversity = topics don't share vocabulary (good separation).
    """
    all_words = [w for topic in topics for w in topic]
    unique = len(set(all_words))
    return round(unique / len(all_words), 3)
