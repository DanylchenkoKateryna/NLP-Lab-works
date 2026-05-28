"""
threshold_eval.py — Threshold selection utilities for Lab 7.

Provides helpers to find optimal thresholds on a validation set
under different PR objectives (precision-first, recall-first, F1-balanced).
"""

import numpy as np
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score


def find_threshold_for_recall(y_true_binary, scores, min_recall=0.80):
    """
    Return the highest threshold at which recall >= min_recall.
    Useful for recall-first tasks (FN are expensive).
    """
    precision, recall, thresholds = precision_recall_curve(y_true_binary, scores)
    # thresholds has len = len(precision) - 1
    mask = recall[:-1] >= min_recall
    if not mask.any():
        return float(thresholds[0])
    return float(thresholds[mask][-1])


def find_threshold_for_precision(y_true_binary, scores, min_precision=0.90):
    """
    Return the lowest threshold at which precision >= min_precision.
    Useful for precision-first tasks (FP are expensive).
    """
    precision, recall, thresholds = precision_recall_curve(y_true_binary, scores)
    mask = precision[:-1] >= min_precision
    if not mask.any():
        return float(thresholds[-1])
    return float(thresholds[mask][0])


def find_best_f1_threshold(y_true_binary, scores):
    """Return the threshold that maximises binary F1 on the provided set."""
    precision, recall, thresholds = precision_recall_curve(y_true_binary, scores)
    with np.errstate(divide='ignore', invalid='ignore'):
        f1 = np.where(
            (precision[:-1] + recall[:-1]) > 0,
            2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1]),
            0.0,
        )
    best_idx = int(np.argmax(f1))
    return float(thresholds[best_idx]), float(f1[best_idx])


def threshold_summary(y_true_binary, scores, thresholds, names=None):
    """
    Print a table comparing multiple thresholds.

    Parameters
    ----------
    thresholds : list of float
    names      : optional list of str labels (same length as thresholds)
    """
    if names is None:
        names = [f'thr={t:.3f}' for t in thresholds]

    header = f"{'Name':<20} {'Threshold':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'#Pos':>6}"
    print(header)
    print('-' * len(header))
    rows = []
    for name, thr in zip(names, thresholds):
        y_pred = (np.asarray(scores) >= thr).astype(int)
        prec = precision_score(y_true_binary, y_pred, zero_division=0)
        rec  = recall_score(y_true_binary, y_pred, zero_division=0)
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        n_pos = int(y_pred.sum())
        print(f'{name:<20} {thr:>9.4f} {prec:>10.4f} {rec:>8.4f} {f1:>8.4f} {n_pos:>6}')
        rows.append(dict(name=name, threshold=thr, precision=prec, recall=rec,
                         f1=f1, n_predicted_positive=n_pos))
    return rows
