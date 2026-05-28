"""
svm_experiments.py — Linear SVM experiments for Lab 7.

Provides reusable helpers for:
  - TF-IDF + LogisticRegression baseline (ЛР6 reference)
  - TF-IDF + LinearSVC
  - FeatureUnion word + char TF-IDF + LinearSVC
  - confusion matrix plot
  - PR-curve plot
  - threshold evaluation
"""

import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.sparse import hstack

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    average_precision_score,
)
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

_FOOTER_RE = re.compile(r'\s*(Newsgroup:\s*\S+|[Dd]ocument_id:\s*\d+)\s*', re.I)


def strip_footer(text: str) -> str:
    return _FOOTER_RE.sub(' ', str(text)).strip()


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def run_logreg_baseline(X_train, y_train, X_val, y_val, X_test, y_test,
                        label_names, ngram_range=(1, 2), max_features=20_000,
                        class_weight=None, C=1.0, seed=42):
    """TF-IDF word n-grams + Logistic Regression. Returns fitted pipe + eval dicts."""
    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', ngram_range=ngram_range,
            max_features=max_features, sublinear_tf=True, min_df=2,
        )),
        ('clf', LogisticRegression(
            C=C, max_iter=500, random_state=seed,
            class_weight=class_weight, solver='lbfgs',
        )),
    ])
    pipe.fit(X_train, y_train)
    val_res  = _evaluate(pipe, X_val,  y_val,  label_names)
    test_res = _evaluate(pipe, X_test, y_test, label_names)
    return pipe, val_res, test_res


def run_linear_svc(X_train, y_train, X_val, y_val, X_test, y_test,
                   label_names, ngram_range=(1, 2), max_features=20_000,
                   class_weight=None, C=1.0):
    """TF-IDF word n-grams + LinearSVC. Returns fitted pipe + eval dicts."""
    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer='word', ngram_range=ngram_range,
            max_features=max_features, sublinear_tf=True, min_df=2,
        )),
        ('clf', LinearSVC(C=C, class_weight=class_weight, max_iter=2000)),
    ])
    pipe.fit(X_train, y_train)
    val_res  = _evaluate(pipe, X_val,  y_val,  label_names)
    test_res = _evaluate(pipe, X_test, y_test, label_names)
    return pipe, val_res, test_res


def run_svc_word_char(X_train, y_train, X_val, y_val, X_test, y_test,
                      label_names, word_ngram=(1, 2), char_ngram=(3, 5),
                      max_features=20_000, class_weight=None, C=1.0):
    """
    Manual FeatureUnion: word TF-IDF + char_wb TF-IDF, stacked horizontally,
    then LinearSVC.  Returns fitted vectorizers, clf, and eval dicts.
    """
    vec_word = TfidfVectorizer(
        analyzer='word', ngram_range=word_ngram,
        max_features=max_features, sublinear_tf=True, min_df=2,
    )
    vec_char = TfidfVectorizer(
        analyzer='char_wb', ngram_range=char_ngram,
        max_features=max_features, sublinear_tf=True, min_df=2,
    )
    clf = LinearSVC(C=C, class_weight=class_weight, max_iter=2000)

    Xw_train = vec_word.fit_transform(X_train)
    Xc_train = vec_char.fit_transform(X_train)
    X_train_combined = hstack([Xw_train, Xc_train])
    clf.fit(X_train_combined, y_train)

    def _transform_and_eval(X_raw, y_true):
        Xw = vec_word.transform(X_raw)
        Xc = vec_char.transform(X_raw)
        X_combined = hstack([Xw, Xc])
        y_pred = clf.predict(X_combined)
        scores = clf.decision_function(X_combined)
        return {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'macro_f1': float(f1_score(y_true, y_pred, average='macro')),
            'report': classification_report(y_true, y_pred, target_names=label_names),
            'y_pred': y_pred,
            'scores': scores,
            'X_combined': X_combined,
        }

    val_res  = _transform_and_eval(X_val,  y_val)
    test_res = _transform_and_eval(X_test, y_test)
    return (vec_word, vec_char, clf), val_res, test_res


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_confusion_matrix(y_true, y_pred, label_names, title='', ax=None, save_path=None):
    """Plot a seaborn heatmap confusion matrix. Returns the axes."""
    short = [n.split('.')[-1] for n in label_names]
    cm = confusion_matrix(y_true, y_pred)
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=short, yticklabels=short, ax=ax)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    if save_path:
        ax.figure.savefig(save_path, dpi=120, bbox_inches='tight')
    return ax


def plot_pr_curve(y_true_binary, scores_1d, class_name='class', ax=None,
                  thresholds_to_mark=None):
    """
    Plot a Precision-Recall curve for a binary (OvR) problem.

    y_true_binary : array of 0/1  (1 = the class of interest)
    scores_1d     : decision_function scores for that class
    thresholds_to_mark : list of (threshold, label) tuples to annotate
    """
    precision, recall, thresholds = precision_recall_curve(y_true_binary, scores_1d)
    ap = average_precision_score(y_true_binary, scores_1d)

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))

    ax.plot(recall, precision, lw=2, label=f'{class_name}  AP={ap:.3f}')
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(f'PR Curve — {class_name} (OvR)')
    ax.legend(loc='lower left')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    ax.grid(alpha=0.3)

    if thresholds_to_mark:
        for thr, lbl in thresholds_to_mark:
            # find index closest to this threshold
            idx = np.searchsorted(thresholds, thr)
            idx = min(idx, len(precision) - 2)
            ax.annotate(
                lbl,
                xy=(recall[idx], precision[idx]),
                xytext=(recall[idx] + 0.04, precision[idx] - 0.06),
                arrowprops=dict(arrowstyle='->', color='red'),
                color='red', fontsize=9,
            )
            ax.scatter([recall[idx]], [precision[idx]], color='red', zorder=5)

    return ax, precision, recall, thresholds


# ---------------------------------------------------------------------------
# Threshold evaluation
# ---------------------------------------------------------------------------

def evaluate_thresholds(y_true_binary, scores_1d, thresholds, class_name='class'):
    """
    For each threshold, compute precision, recall, F1.
    Returns a list of dicts, one per threshold.
    """
    from sklearn.metrics import precision_score, recall_score

    rows = []
    for thr in thresholds:
        y_pred_bin = (scores_1d >= thr).astype(int)
        prec = precision_score(y_true_binary, y_pred_bin, zero_division=0)
        rec  = recall_score(y_true_binary, y_pred_bin, zero_division=0)
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        rows.append({
            'class': class_name,
            'threshold': round(float(thr), 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1': round(f1, 4),
            'n_predicted_positive': int(y_pred_bin.sum()),
        })
    return rows


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _evaluate(pipe, X, y, label_names):
    y_pred = pipe.predict(X)
    scores = None
    if hasattr(pipe.named_steps['clf'], 'decision_function'):
        scores = pipe.decision_function(X)
    return {
        'accuracy': float(accuracy_score(y, y_pred)),
        'macro_f1': float(f1_score(y, y_pred, average='macro')),
        'report': classification_report(y, y_pred, target_names=label_names),
        'y_pred': y_pred,
        'scores': scores,
    }
