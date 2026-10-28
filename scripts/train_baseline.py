#!/usr/bin/env python
"""train_baseline.py
Baseline training pipeline for PostureAI.
* Loads engineered CSV
* Validates data integrity
* Performs subject‑wise train/val/test split (70/15/15%)
* Trains a RandomForestClassifier
* Saves model and (optional) preprocessing pipeline
* Generates evaluation report and confusion matrix image
"""

import os
import json
import pathlib
import argparse
from collections import Counter

import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "multiposture_engineered.csv"
MODEL_DIR = pathlib.Path(__file__).resolve().parents[1] / "ml" / "models"
REPORT_DIR = pathlib.Path(__file__).resolve().parents[1] / "reports" / "ml"
SEED = 42
TRAIN_SIZE = 0.70
VAL_SIZE = 0.15  # of total; test gets remaining

FEATURE_COLS = [
    "head_pitch",
    "head_roll",
    "forward_head_displacement",
    "torso_pitch",
    "torso_lateral_tilt",
    "torso_rotation",
    "shoulder_asymmetry",
    "upper_arm_elevation",
]
TARGET_COL = "upperbody_label"

def load_and_validate(path: pathlib.Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")
    df = pd.read_csv(path)
    # Expected columns
    expected = set(["subject", TARGET_COL] + FEATURE_COLS)
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    # Numeric check for features – ensure all feature columns are numeric
    if not df[FEATURE_COLS].dtypes.apply(lambda dt: np.issubdtype(dt, np.number)).all():
        raise ValueError("Non‑numeric values detected in feature columns")
    # Missing / infinite values
    if df[FEATURE_COLS].isnull().any().any():
        raise ValueError("NaN values found in feature columns")
    if np.isinf(df[FEATURE_COLS].values).any():
        raise ValueError("Infinite values found in feature columns")
    # Label sanity
    if df[TARGET_COL].isnull().any():
        raise ValueError("Missing labels detected")
    # Subject sanity
    if df["subject"].isnull().any():
        raise ValueError("Missing subject identifiers")
    return df

def subject_wise_split(df: pd.DataFrame, seed: int = SEED):
    subjects = df["subject"].unique()
    gss = GroupShuffleSplit(n_splits=1, train_size=TRAIN_SIZE, random_state=seed)
    train_idx, temp_idx = next(gss.split(df, groups=df["subject"]))
    train_df = df.iloc[train_idx]
    temp_df = df.iloc[temp_idx]
    # Now split temp into val and test proportionally
    val_frac = VAL_SIZE / (1 - TRAIN_SIZE)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=val_frac, random_state=seed)
    val_idx, test_idx = next(gss2.split(temp_df, groups=temp_df["subject"]))
    val_df = temp_df.iloc[val_idx]
    test_df = temp_df.iloc[test_idx]
    # Verify no overlap of subjects
    assert set(train_df["subject"]).isdisjoint(set(val_df["subject"]))
    assert set(train_df["subject"]).isdisjoint(set(test_df["subject"]))
    assert set(val_df["subject"]).isdisjoint(set(test_df["subject"]))
    return train_df, val_df, test_df

def train_random_forest(X_train, y_train, random_state=SEED):
    clf = RandomForestClassifier(n_estimators=200, random_state=random_state, n_jobs=-1)
    clf.fit(X_train, y_train)
    return clf

def evaluate_model(clf, X, y, split_name="test"):
    preds = clf.predict(X)
    probs = clf.predict_proba(X)
    acc = accuracy_score(y, preds)
    prec = precision_score(y, preds, average="weighted", zero_division=0)
    rec = recall_score(y, preds, average="weighted", zero_division=0)
    f1 = f1_score(y, preds, average="weighted", zero_division=0)
    report = classification_report(y, preds, zero_division=0)
    conf_mat = confusion_matrix(y, preds)
    metrics = {
        "split": split_name,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "classification_report": report,
        "confusion_matrix": conf_mat.tolist(),
    }
    return metrics, preds, probs

def save_report(metrics_dict, report_path: pathlib.Path):
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, indent=2)

def plot_confusion(conf_mat, labels, out_path: pathlib.Path):
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_mat, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Train baseline posture model.")
    parser.add_argument(
        "--data",
        type=pathlib.Path,
        default=pathlib.Path("data/posture_extended_dataset.csv") if pathlib.Path("data/posture_extended_dataset.csv").exists() else DATA_PATH,
        help="Path to engineered CSV dataset",
    )
    args = parser.parse_args()

    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    print(f"Loading dataset from: {args.data}")
    df = load_and_validate(args.data)
    train_df, val_df, test_df = subject_wise_split(df)
    # Save split subject lists for documentation
    split_info = {
        "train_subjects": sorted(train_df["subject"].unique().tolist()),
        "val_subjects": sorted(val_df["subject"].unique().tolist()),
        "test_subjects": sorted(test_df["subject"].unique().tolist()),
    }
    with open(REPORT_DIR / "split_subjects.json", "w", encoding="utf-8") as f:
        json.dump(split_info, f, indent=2)
    X_train = train_df[FEATURE_COLS]
    y_train = train_df[TARGET_COL]
    X_val = val_df[FEATURE_COLS]
    y_val = val_df[TARGET_COL]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df[TARGET_COL]

    model = train_random_forest(X_train, y_train)
    # Save model
    joblib.dump(model, MODEL_DIR / "posture_model.joblib")
    joblib.dump(model, MODEL_DIR / "selected_development_model.joblib")

    # Evaluate on each split
    metrics = {}
    for split_name, X, y in [
        ("train", X_train, y_train),
        ("validation", X_val, y_val),
        ("test", X_test, y_test),
    ]:
        m, _, _ = evaluate_model(model, X, y, split_name)
        metrics[split_name] = m
    # Save metrics JSON
    save_report(metrics, REPORT_DIR / "evaluation.json")
    # Human‑readable text report
    with open(REPORT_DIR / "evaluation.txt", "w", encoding="utf-8") as f:
        for split, vals in metrics.items():
            f.write(f"=== {split.upper()} ===\n")
            f.write(f"Accuracy : {vals['accuracy']:.4f}\n")
            f.write(f"Precision: {vals['precision']:.4f}\n")
            f.write(f"Recall   : {vals['recall']:.4f}\n")
            f.write(f"F1‑score : {vals['f1']:.4f}\n\n")
            f.write(vals['classification_report'])
            f.write("\n\n")
    # Plot confusion matrix for test set
    _, test_preds, _ = evaluate_model(model, X_test, y_test, "test")
    conf = confusion_matrix(y_test, test_preds)
    labels = sorted(y_test.unique())
    plot_confusion(conf, labels, REPORT_DIR / "confusion_matrix.png")
    print("Training complete. Model saved to", MODEL_DIR / "posture_model.joblib")
    print("Evaluation JSON saved to", REPORT_DIR / "evaluation.json")
    print("Confusion matrix image saved to", REPORT_DIR / "confusion_matrix.png")

if __name__ == "__main__":
    main()
