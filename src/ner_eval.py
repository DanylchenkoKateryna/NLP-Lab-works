"""
ner_eval.py — Evaluation utilities for NER baseline vs hybrid comparison.

Provides:
- Gold set definition (25 hand-annotated sentences from 20 Newsgroups)
- correct / missed / false_positive counting per entity type
- rough precision / recall per type
- structured error analysis with error categories
- audit_summary generator
"""

import re
import pandas as pd
from typing import Optional


# ── Gold evaluation set ──────────────────────────────────────────────────────
# 25 sentences drawn from the 20 Newsgroups corpus (alt.atheism,
# sci.electronics, soc.religion.christian).  Gold entities were
# annotated manually; format: (text, [(entity_text, label), ...])

GOLD_SET = [
    # ── sci.electronics ──────────────────────────────────────────────────────
    (
        "I'm using a 2N2222 transistor and a 10k resistor to drive an LED.",
        [("2N2222 transistor", "ELECTRONICS_COMPONENT"), ("resistor", "ELECTRONICS_COMPONENT")],
    ),
    (
        "The capacitor across the power supply should be at least 100uF.",
        [("capacitor", "ELECTRONICS_COMPONENT")],
    ),
    (
        "A zener diode is used to clamp the voltage at 5.1V.",
        [("zener", "ELECTRONICS_COMPONENT"), ("diode", "ELECTRONICS_COMPONENT")],
    ),
    (
        "I have a question about op-amp circuits for a signal conditioning stage.",
        [("op-amp", "ELECTRONICS_COMPONENT")],
    ),
    (
        "The schematic shows a bridge rectifier followed by a voltage regulator.",
        [("schematic", "ELECTRONICS_COMPONENT"), ("rectifier", "ELECTRONICS_COMPONENT"),
         ("regulator", "ELECTRONICS_COMPONENT")],
    ),
    (
        "Thu, 15 Apr 1993 09:45:12 -0500 — anyone know a good oscilloscope brand?",
        [("Thu, 15 Apr 1993 09:45:12 -0500", "DATE"), ("oscilloscope", "ELECTRONICS_COMPONENT")],
    ),
    (
        "Intel released its first microprocessor in November 1971.",
        [("Intel", "ORG"), ("November 1971", "DATE")],
    ),
    (
        "The MIT Media Lab published a paper on signal processing last year.",
        [("MIT Media Lab", "ORG")],
    ),
    (
        "Hewlett-Packard has a good oscilloscope that costs about $2,500.",
        [("Hewlett-Packard", "ORG"), ("$2,500", "MONEY"), ("oscilloscope", "ELECTRONICS_COMPONENT")],
    ),
    # ── soc.religion.christian ───────────────────────────────────────────────
    (
        "Jesus Christ is the Son of God according to Christian belief.",
        [("Jesus Christ", "PERSON"), ("God", "PERSON"), ("Christian", "NORP")],
    ),
    (
        "Paul wrote in his letter to the Corinthians about love and faith.",
        [("Paul", "PERSON"), ("Corinthians", "NORP")],
    ),
    (
        "The Virgin Mary is venerated in the Catholic Church.",
        [("Virgin Mary", "PERSON"), ("Catholic Church", "ORG")],
    ),
    (
        "According to the Bible, John the Baptist prepared the way for Jesus.",
        [("John the Baptist", "PERSON"), ("Jesus", "PERSON")],
    ),
    (
        "The Holy Spirit descended on the apostles at Pentecost.",
        [("Holy Spirit", "PERSON"), ("Pentecost", "DATE")],
    ),
    (
        "Pope John Paul II visited Poland in June 1979.",
        [("Pope John Paul II", "PERSON"), ("Poland", "GPE"), ("June 1979", "DATE")],
    ),
    (
        "Mother Teresa was born on August 26, 1910 in Skopje.",
        [("Mother Teresa", "PERSON"), ("August 26, 1910", "DATE"), ("Skopje", "GPE")],
    ),
    (
        "Saint Peter was crucified upside-down in Rome around 64 AD.",
        [("Saint Peter", "PERSON"), ("Rome", "GPE"), ("64 AD", "DATE")],
    ),
    # ── alt.atheism ──────────────────────────────────────────────────────────
    (
        "Fri, 23 Apr 1993 14:22:01 GMT — mathew@mantis.co.uk wrote:",
        [("Fri, 23 Apr 1993 14:22:01 GMT", "DATE")],
    ),
    (
        "The American Atheists organization was founded by Madalyn Murray O'Hair.",
        [("American Atheists", "ORG"), ("Madalyn Murray O'Hair", "PERSON")],
    ),
    (
        "David Hume argued that miracles are highly improbable in his 1748 essay.",
        [("David Hume", "PERSON"), ("1748", "DATE")],
    ),
    (
        "The Council of Nicaea in 325 AD defined the doctrine of the Trinity.",
        [("Council of Nicaea", "ORG"), ("325 AD", "DATE")],
    ),
    (
        "Richard Dawkins published The God Delusion in 2006.",
        [("Richard Dawkins", "PERSON"), ("2006", "DATE")],
    ),
    (
        "According to Islam, Muhammad received the Quran in Arabia during the 7th century.",
        [("Islam", "NORP"), ("Muhammad", "PERSON"), ("Arabia", "GPE"), ("7th century", "DATE")],
    ),
    (
        "The University of California at Berkeley has a philosophy department.",
        [("University of California at Berkeley", "ORG")],
    ),
    (
        "Wed, 14 Apr 1993 20:11:04 -0400 — posted from Cleveland State University.",
        [("Wed, 14 Apr 1993 20:11:04 -0400", "DATE"), ("Cleveland State University", "ORG")],
    ),
]


# ── Evaluation helpers ────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Lowercase + collapse whitespace for fuzzy matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def match_entity(pred_text: str, gold_text: str, gold_label: str, pred_label: str) -> str:
    """
    Classify a prediction vs gold match.

    Returns one of:
        'exact'      — text and label match
        'type_error' — text matches but label differs
        'boundary'   — partial text overlap
        'none'       — no match
    """
    pn = normalize(pred_text)
    gn = normalize(gold_text)

    if pn == gn:
        return "exact" if pred_label == gold_label else "type_error"
    if pn in gn or gn in pn:
        return "boundary"
    return "none"


def evaluate_single(
    predicted: list[dict],
    gold: list[tuple[str, str]],
) -> dict:
    """
    Compare predicted entities against gold for one sentence.

    Returns dict:
        correct, missed, false_positive,
        type_errors, boundary_errors,
        details (list of result dicts)
    """
    gold_remaining = list(gold)  # [(text, label), ...]
    pred_remaining = list(predicted)

    matched_gold_idx: set[int] = set()
    matched_pred_idx: set[int] = set()
    details = []

    # First pass: exact matches
    for pi, p in enumerate(pred_remaining):
        for gi, (gt, gl) in enumerate(gold_remaining):
            if gi in matched_gold_idx:
                continue
            if normalize(p["text"]) == normalize(gt):
                if p["label"] == gl:
                    details.append({
                        "pred_text": p["text"], "pred_label": p["label"],
                        "gold_text": gt, "gold_label": gl,
                        "result": "correct",
                    })
                else:
                    details.append({
                        "pred_text": p["text"], "pred_label": p["label"],
                        "gold_text": gt, "gold_label": gl,
                        "result": "type_error",
                    })
                matched_gold_idx.add(gi)
                matched_pred_idx.add(pi)
                break

    # Second pass: boundary matches
    for pi, p in enumerate(pred_remaining):
        if pi in matched_pred_idx:
            continue
        for gi, (gt, gl) in enumerate(gold_remaining):
            if gi in matched_gold_idx:
                continue
            pn, gn = normalize(p["text"]), normalize(gt)
            if pn in gn or gn in pn:
                details.append({
                    "pred_text": p["text"], "pred_label": p["label"],
                    "gold_text": gt, "gold_label": gl,
                    "result": "boundary_error",
                })
                matched_gold_idx.add(gi)
                matched_pred_idx.add(pi)
                break

    # Missed gold entities
    for gi, (gt, gl) in enumerate(gold_remaining):
        if gi not in matched_gold_idx:
            details.append({
                "pred_text": None, "pred_label": None,
                "gold_text": gt, "gold_label": gl,
                "result": "missed",
            })

    # False positives
    for pi, p in enumerate(pred_remaining):
        if pi not in matched_pred_idx:
            details.append({
                "pred_text": p["text"], "pred_label": p["label"],
                "gold_text": None, "gold_label": None,
                "result": "false_positive",
            })

    counts = {r: sum(1 for d in details if d["result"] == r)
              for r in ["correct", "missed", "type_error",
                        "boundary_error", "false_positive"]}
    return {"counts": counts, "details": details}


def evaluate_corpus(
    predictions: list[list[dict]],
    gold_set: list[tuple[str, list[tuple[str, str]]]] = None,
) -> dict:
    """
    Evaluate predictions against the gold set.

    Returns aggregated counts + per-type breakdown + rough precision/recall.
    """
    if gold_set is None:
        gold_set = GOLD_SET

    all_details = []
    total = {"correct": 0, "missed": 0, "type_error": 0,
             "boundary_error": 0, "false_positive": 0}

    for (text, gold_ents), pred_ents in zip(gold_set, predictions):
        res = evaluate_single(pred_ents, gold_ents)
        for k in total:
            total[k] += res["counts"].get(k, 0)
        for d in res["details"]:
            d["text_snippet"] = text[:80]
        all_details.extend(res["details"])

    # Rough precision and recall
    tp = total["correct"]
    fp = total["false_positive"] + total["type_error"] + total["boundary_error"]
    fn = total["missed"] + total["type_error"] + total["boundary_error"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Per-type breakdown
    by_type: dict[str, dict] = {}
    for d in all_details:
        label = d.get("gold_label") or d.get("pred_label") or "?"
        if label not in by_type:
            by_type[label] = {"correct": 0, "missed": 0, "fp": 0, "type_err": 0, "boundary": 0}
        r = d["result"]
        if r == "correct":
            by_type[label]["correct"] += 1
        elif r == "missed":
            by_type[label]["missed"] += 1
        elif r == "false_positive":
            by_type[label]["fp"] += 1
        elif r == "type_error":
            by_type[label]["type_err"] += 1
        elif r == "boundary_error":
            by_type[label]["boundary"] += 1

    return {
        "totals":     total,
        "precision":  round(precision, 3),
        "recall":     round(recall, 3),
        "f1":         round(f1, 3),
        "by_type":    by_type,
        "details":    all_details,
    }


def print_eval_summary(result: dict, label: str = "Evaluation") -> None:
    t = result["totals"]
    print(f"{'='*55}")
    print(f"{label}")
    print(f"{'='*55}")
    print(f"  Correct       : {t['correct']}")
    print(f"  Missed        : {t['missed']}")
    print(f"  Type errors   : {t['type_error']}")
    print(f"  Boundary errs : {t['boundary_error']}")
    print(f"  False positives: {t['false_positive']}")
    print(f"  Rough Precision: {result['precision']:.3f}")
    print(f"  Rough Recall   : {result['recall']:.3f}")
    print(f"  Rough F1       : {result['f1']:.3f}")
    print()
    print("  Per-type breakdown:")
    for lbl, cnts in sorted(result["by_type"].items()):
        print(f"    {lbl:<25s} correct={cnts['correct']} missed={cnts['missed']} "
              f"fp={cnts['fp']} type_err={cnts['type_err']} boundary={cnts['boundary']}")
    print()


def error_analysis_table(details: list[dict]) -> pd.DataFrame:
    """Build a tidy DataFrame of all error details."""
    rows = []
    for d in details:
        if d["result"] != "correct":
            rows.append({
                "snippet":    d.get("text_snippet", "")[:70],
                "gold_text":  d.get("gold_text", ""),
                "gold_label": d.get("gold_label", ""),
                "pred_text":  d.get("pred_text", ""),
                "pred_label": d.get("pred_label", ""),
                "error_type": d["result"],
            })
    return pd.DataFrame(rows)


# ── Error category classification ─────────────────────────────────────────────

ERROR_CATEGORIES = {
    "missed":         "missed domain entity",
    "false_positive": "false positive",
    "type_error":     "type error",
    "boundary_error": "boundary error",
}


def classify_error(row: dict) -> str:
    return ERROR_CATEGORIES.get(row.get("error_type", ""), "other")


# ── audit_summary generator ───────────────────────────────────────────────────

def generate_audit_md(results: dict, output_path: str) -> None:
    """Write docs/audit_summary_lab10.md."""
    lines = [
        "# Audit Summary — Lab 10: NER Pipeline + Hybrid Rules\n",
        f"**Date:** 2026-05-29\n",
        "",
        "## 1. Pipeline",
        f"- **Model:** {results.get('model', 'spaCy en_core_web_sm')}",
        f"- **Language:** English",
        f"- **Entity labels (baseline):** {results.get('entity_labels', '')}",
        "",
        "## 2. Important Entity Types for This Corpus",
    ]
    for e in results.get("important_entities", []):
        lines.append(f"- {e}")

    lines += [
        "",
        "## 3. What Baseline Found Well",
    ]
    for e in results.get("baseline_good", []):
        lines.append(f"- {e}")

    lines += [
        "",
        "## 4. What Baseline Missed",
    ]
    for e in results.get("baseline_missed", []):
        lines.append(f"- {e}")

    lines += [
        "",
        "## 5. Hybrid Rules Added",
    ]
    for r in results.get("rules", []):
        lines.append(f"- **{r['name']}**: {r['description']}")

    lines += [
        "",
        "## 6. What Rules Improved",
        results.get("rules_improved", ""),
        "",
        "## 7. Error Categories (Most Frequent)",
    ]
    for e in results.get("error_categories", []):
        lines.append(f"- {e}")

    lines += [
        "",
        "## 8. Evaluation Results",
        "### Baseline",
        f"- Correct: {results.get('baseline_correct', 'N/A')}",
        f"- Missed:  {results.get('baseline_missed_count', 'N/A')}",
        f"- FP:      {results.get('baseline_fp', 'N/A')}",
        f"- Rough P/R/F1: {results.get('baseline_prf', 'N/A')}",
        "### Hybrid",
        f"- Correct: {results.get('hybrid_correct', 'N/A')}",
        f"- Missed:  {results.get('hybrid_missed_count', 'N/A')}",
        f"- FP:      {results.get('hybrid_fp', 'N/A')}",
        f"- Rough P/R/F1: {results.get('hybrid_prf', 'N/A')}",
        "",
        "## 9. What to Fix Next",
    ]
    for s in results.get("next_steps", []):
        lines.append(f"- {s}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved: {output_path}")
