"""
ner_pipeline.py — spaCy NER pipeline loader and inference utilities.

Loads en_core_web_sm (auto-downloads if missing), runs NER inference,
returns structured entity dicts for downstream evaluation and hybrid rules.
"""

import re
import spacy
from typing import Optional


# ── Model loading ────────────────────────────────────────────────────────────

def load_spacy(model_name: str = "en_core_web_sm") -> spacy.language.Language:
    """
    Load a spaCy model, downloading it if not installed.

    Parameters
    ----------
    model_name : str
        spaCy model name (default: en_core_web_sm).

    Returns
    -------
    spacy.Language
    """
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model '{model_name}' not found — downloading...")
        import subprocess, sys
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            check=True
        )
        nlp = spacy.load(model_name)
    return nlp


# ── Inference ────────────────────────────────────────────────────────────────

def run_ner(nlp: spacy.language.Language, text: str) -> list[dict]:
    """
    Run NER on a single text string.

    Returns list of entity dicts:
        {text, label, start_char, end_char}
    """
    doc = nlp(text)
    return [
        {
            "text":       ent.text,
            "label":      ent.label_,
            "start_char": ent.start_char,
            "end_char":   ent.end_char,
        }
        for ent in doc.ents
    ]


def run_ner_batch(
    nlp: spacy.language.Language,
    texts: list[str],
    batch_size: int = 32,
) -> list[list[dict]]:
    """
    Run NER on a list of texts (batched for efficiency).

    Returns list of entity lists (one per text).
    """
    results = []
    for doc in nlp.pipe(texts, batch_size=batch_size):
        results.append([
            {
                "text":       ent.text,
                "label":      ent.label_,
                "start_char": ent.start_char,
                "end_char":   ent.end_char,
            }
            for ent in doc.ents
        ])
    return results


# ── Display helpers ──────────────────────────────────────────────────────────

def print_entities(text: str, entities: list[dict], max_text: int = 100) -> None:
    """Pretty-print inference output for a single text."""
    snippet = text[:max_text].replace("\n", " ")
    print(f"Text  : {snippet}")
    if entities:
        for e in entities:
            print(f"  [{e['label']:12s}] {e['text']!r}")
    else:
        print("  (no entities found)")
    print()


def entities_to_set(entities: list[dict]) -> set[tuple[str, str]]:
    """Convert entity list to a set of (text_lower, label) tuples for comparison."""
    return {(e["text"].lower(), e["label"]) for e in entities}


# ── Model info ───────────────────────────────────────────────────────────────

def model_info(nlp: spacy.language.Language) -> dict:
    """Return brief info about the loaded pipeline."""
    ner = nlp.get_pipe("ner") if nlp.has_pipe("ner") else None
    return {
        "model_name":   nlp.meta.get("name", "?"),
        "lang":         nlp.meta.get("lang", "?"),
        "version":      nlp.meta.get("version", "?"),
        "components":   nlp.pipe_names,
        "entity_labels": list(ner.labels) if ner else [],
    }


def print_model_info(info: dict) -> None:
    print(f"Model        : {info['model_name']}  v{info['version']}  ({info['lang']})")
    print(f"Components   : {info['components']}")
    print(f"Entity labels: {info['entity_labels']}")
    print()
