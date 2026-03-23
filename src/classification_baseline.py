"""
classification_baseline.py — TF-IDF + Logistic Regression baseline (Lab 6)

Provides a clean, reusable pipeline for 3-class newsgroup classification.
"""

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

_FOOTER_RE = re.compile(r'\s*(Newsgroup:\s*\S+|[Dd]ocument_id:\s*\d+)\s*', re.I)


def strip_footer(text: str) -> str:
    """Remove 'Newsgroup: X' and 'document_id: N' metadata appended during data collection."""
    return _FOOTER_RE.sub(' ', str(text)).strip()


def make_pipeline(ngram_range=(1, 1), max_features=20_000, C=1.0,
                  class_weight=None, max_iter=500, seed=42) -> Pipeline:
    """TF-IDF → LogisticRegression sklearn Pipeline."""
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', ngram_range=ngram_range,
            max_features=max_features, sublinear_tf=True, min_df=2,
        )),
        ('clf', LogisticRegression(
            C=C, max_iter=max_iter, random_state=seed,
            class_weight=class_weight, solver='lbfgs', multi_class='auto',
        )),
    ])


def evaluate(pipe, X, y, label_names=None) -> dict:
    """Returns accuracy, macro_f1, full report string, y_pred array."""
    y_pred = pipe.predict(X)
    return {
        'accuracy': accuracy_score(y, y_pred),
        'macro_f1': f1_score(y, y_pred, average='macro'),
        'report': classification_report(y, y_pred, target_names=label_names),
        'y_pred': y_pred,
    }


def top_features_per_class(pipe, label_names, n=10) -> dict:
    """Top-n positive LR features per class. Returns {label: [(token, weight), ...]}."""
    features = pipe.named_steps['tfidf'].get_feature_names_out()
    result = {}
    for i, label in enumerate(label_names):
        coefs = pipe.named_steps['clf'].coef_[i]
        idx = np.argsort(coefs)[::-1][:n]
        result[label] = [(features[j], float(coefs[j])) for j in idx]
    return result
