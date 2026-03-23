"""
split.py — Deterministic train/val/test splitting (Lab 5)

Strategy: stratified random split (preserves class distribution across splits).
Splits are reproducible: same seed → same result.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split


def make_splits(
    df: pd.DataFrame,
    label_col: str = "label_id",
    text_col: str = "text_v2",
    strategy: str = "stratified",
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Split df into train / val / test with stratification on label_col.

    Duplicate-aware: all rows sharing the same text content are assigned
    to the same split, preventing exact-duplicate leakage across splits.

    Returns {"train": df_train, "val": df_val, "test": df_test}.
    """
    if strategy != "stratified":
        raise ValueError(f"Unsupported strategy: '{strategy}'.")

    test_ratio = 1.0 - train_ratio - val_ratio

    # Assign a group ID to every unique text (dedup-aware grouping)
    df = df.copy()
    df["_text_group"] = df[text_col].fillna("").astype(str)
    # For each group keep the majority label for stratification
    group_label = (
        df.groupby("_text_group")[label_col]
        .agg(lambda s: s.mode()[0])
        .reset_index()
        .rename(columns={label_col: "_group_label"})
    )

    # Split at the group level (ensures all copies of a text stay in one split)
    g_train, g_temp = train_test_split(
        group_label, test_size=(val_ratio + test_ratio),
        stratify=group_label["_group_label"], random_state=seed,
    )
    relative_val = val_ratio / (val_ratio + test_ratio)
    g_val, g_test = train_test_split(
        g_temp, test_size=(1 - relative_val),
        stratify=g_temp["_group_label"], random_state=seed,
    )

    train_texts = set(g_train["_text_group"])
    val_texts   = set(g_val["_text_group"])
    test_texts  = set(g_test["_text_group"])

    df_train = df[df["_text_group"].isin(train_texts)].drop(columns=["_text_group"])
    df_val   = df[df["_text_group"].isin(val_texts)].drop(columns=["_text_group"])
    df_test  = df[df["_text_group"].isin(test_texts)].drop(columns=["_text_group"])

    return {"train": df_train.reset_index(drop=True),
            "val":   df_val.reset_index(drop=True),
            "test":  df_test.reset_index(drop=True)}


def save_splits(
    splits: Dict[str, pd.DataFrame],
    out_dir: str | Path,
    id_col: str = "id",
    label_col: str = "label_id",
    category_col: str = "category",
    strategy: str = "stratified",
    seed: int = 42,
) -> Path:
    """
    Save split IDs to .txt files and a manifest JSON.

    Files written:
      <out_dir>/splits_train_ids.txt
      <out_dir>/splits_val_ids.txt
      <out_dir>/splits_test_ids.txt
      <out_dir>/splits_manifest_lab5.json  (also written to docs/ if it exists)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sizes = {}
    class_dist = {}
    for name, df_split in splits.items():
        ids_path = out_dir / f"splits_{name}_ids.txt"
        ids_path.write_text("\n".join(str(i) for i in df_split[id_col]), encoding="utf-8")
        sizes[name] = len(df_split)
        class_dist[name] = df_split[category_col].value_counts().to_dict()

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "strategy": strategy,
        "seed": seed,
        "ratios": {"train": 0.80, "val": 0.10, "test": 0.10},
        "sizes": sizes,
        "class_distribution": class_dist,
        "columns_used": {"label": label_col, "id": id_col},
        "source_file": "data/processed_v2/processed_v2.csv",
    }

    manifest_path = out_dir / "splits_manifest_lab5.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Mirror manifest to docs/ if available
    docs_dir = out_dir.parent.parent / "docs"
    if docs_dir.exists():
        (docs_dir / "splits_manifest_lab5.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return manifest_path
