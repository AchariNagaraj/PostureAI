#!/usr/bin/env python
"""model_comparison_cv.py
Cross‑validation experiment (Phase 1.5) for PostureAI.
* Uses only development subjects [2,3,4,5,6,7,8,10,11,13]
* 5‑fold GroupKFold (subject‑wise)
* Evaluates five classifiers
* Saves per‑fold subject splits, metrics, confusion matrices, and aggregated results.
"""

import pathlib
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "multiposture_engineered.csv"
REPORT_ROOT = pathlib.Path(__file__).resolve().parents[1] / "reports" / "ml" / "model_comparison"
MODEL_DIR = pathlib.Path(__file__).resolve().parents[1] / "ml" / "models"

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

DEV_SUBJECTS = [2, 3, 4, 5, 6, 7, 8, 10, 11, 13]
TEST_SUBJECTS = [1, 9, 12]

def load_data():
    df = pd.read_csv(DATA_PATH)
    df["subject"] = df["subject"].astype(int)
    return df

def get_folds(df_dev, n_splits=5):
    gkf = GroupKFold(n_splits=n_splits)
    folds = []
    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(df_dev, groups=df_dev["subject"])):
        train_subj = sorted(df_dev.iloc[train_idx]["subject"].unique().tolist())
        val_subj = sorted(df_dev.iloc[val_idx]["subject"].unique().tolist())
        assert set(train_subj).isdisjoint(set(val_subj))
        folds.append({
            "fold": fold_idx,
            "train_idx": train_idx,
            "val_idx": val_idx,
            "train_subjects": train_subj,
            "val_subjects": val_subj,
        })
    return folds

def evaluate_fold(model, X_val, y_val):
    pred = model.predict(X_val)
    prob = model.predict_proba(X_val) if hasattr(model, "predict_proba") else None
    acc = accuracy_score(y_val, pred)
    macro_prec = precision_score(y_val, pred, average="macro", zero_division=0)
    macro_rec = recall_score(y_val, pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_val, pred, average="macro", zero_division=0)
    weighted_prec = precision_score(y_val, pred, average="weighted", zero_division=0)
    weighted_rec = recall_score(y_val, pred, average="weighted", zero_division=0)
    weighted_f1 = f1_score(y_val, pred, average="weighted", zero_division=0)
    class_report = classification_report(y_val, pred, output_dict=True, zero_division=0)
    conf = confusion_matrix(y_val, pred, labels=sorted(y_val.unique()))
    return {
        "accuracy": acc,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_prec,
        "weighted_recall": weighted_rec,
        "weighted_f1": weighted_f1,
        "class_report": class_report,
        "confusion_matrix": conf.tolist(),
        "predictions": pred.tolist(),
        "probabilities": prob.tolist() if prob is not None else None,
    }

def plot_confusion(conf_mat, labels, out_path):
    plt.figure(figsize=(8,6))
    sns.heatmap(conf_mat, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def main():
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    df_dev = df[df["subject"].isin(DEV_SUBJECTS)].reset_index(drop=True)
    df_test = df[df["subject"].isin(TEST_SUBJECTS)].reset_index(drop=True)
    folds = get_folds(df_dev, n_splits=5)
    with open(REPORT_ROOT / "cv_folds.json", "w", encoding="utf-8") as f:
        json.dump({f["fold"]:{"train_subjects":f["train_subjects"],"val_subjects":f["val_subjects"]} for f in folds}, f, indent=2)
    models = {
        "LogisticRegression": Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, random_state=SEED, n_jobs=-1))]),
        "SVM_RBF": Pipeline([("scaler", StandardScaler()), ("clf", SVC(kernel='rbf', probability=True, random_state=SEED))]),
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=SEED)
    }
    cv_results = {name: [] for name in models}
    oof_predictions = {name: [] for name in models}
    oof_true = []
    for fold in folds:
        train_df = df_dev.iloc[fold["train_idx"]]
        val_df = df_dev.iloc[fold["val_idx"]]
        X_train = train_df[FEATURE_COLS]
        y_train = train_df[TARGET_COL]
        X_val = val_df[FEATURE_COLS]
        y_val = val_df[TARGET_COL]
        oof_true.extend(y_val.tolist())
        for name, model in models.items():
            model.fit(X_train, y_train)
            metrics = evaluate_fold(model, X_val, y_val)
            cv_results[name].append(metrics)
            oof_predictions[name].extend(metrics["predictions"])
    aggregate = {}
    for name, folds_metrics in cv_results.items():
        summary = {}
        metric_names = ["accuracy","macro_precision","macro_recall","macro_f1","weighted_precision","weighted_recall","weighted_f1"]
        for m in metric_names:
            vals = [fm[m] for fm in folds_metrics]
            summary[m] = {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1))}
        # per‑class stats
        class_labels = sorted(df_dev[TARGET_COL].unique())
        per_class = {lbl:{"precision":[],"recall":[],"f1":[]} for lbl in class_labels}
        for fm in folds_metrics:
            cr = fm["class_report"]
            for lbl in class_labels:
                lbl_str = str(lbl)
                if lbl_str in cr:
                    per_class[lbl]["precision"].append(cr[lbl_str]["precision"])
                    per_class[lbl]["recall"].append(cr[lbl_str]["recall"])
                    per_class[lbl]["f1"].append(cr[lbl_str]["f1-score"])
        per_class_stats = {}
        for lbl, vals in per_class.items():
            per_class_stats[lbl] = {
                "precision":{"mean":float(np.mean(vals["precision"])),"std":float(np.std(vals["precision"],ddof=1))},
                "recall":{"mean":float(np.mean(vals["recall"])),"std":float(np.std(vals["recall"],ddof=1))},
                "f1":{"mean":float(np.mean(vals["f1"])),"std":float(np.std(vals["f1"],ddof=1))},
            }
        aggregate[name] = {"overall":summary,"per_class":per_class_stats,"fold_metrics":folds_metrics}
        # out‑of‑fold confusion matrix
        conf = confusion_matrix(oof_true, oof_predictions[name], labels=class_labels)
        plot_confusion(conf, class_labels, REPORT_ROOT / f"confusion_oof_{name}.png")
        with open(REPORT_ROOT / f"confusion_oof_{name}.json", "w", encoding="utf-8") as f:
            json.dump(conf.tolist(), f, indent=2)
    # Save JSON & CSV
    with open(REPORT_ROOT / "model_comparison.json", "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)
    rows = []
    for name, agg in aggregate.items():
        o = agg["overall"]
        rows.append({
            "model": name,
            "accuracy_mean": o["accuracy"]["mean"],
            "accuracy_std": o["accuracy"]["std"],
            "macro_f1_mean": o["macro_f1"]["mean"],
            "macro_f1_std": o["macro_f1"]["std"],
            "weighted_f1_mean": o["weighted_f1"]["mean"],
            "weighted_f1_std": o["weighted_f1"]["std"],
        })
    pd.DataFrame(rows).to_csv(REPORT_ROOT / "model_comparison.csv", index=False)
    # Select best model (highest macro F1, then weighted F1)
    best_name = max(rows, key=lambda r: (r["macro_f1_mean"], r["weighted_f1_mean"]))["model"]
    selection = {"selected_model":best_name,"reason":"Highest mean macro F1 (tie‑broken by weighted F1)","seed":SEED,"feature_cols":FEATURE_COLS,"target_col":TARGET_COL,"development_subjects":DEV_SUBJECTS,"final_test_subjects":TEST_SUBJECTS}
    with open(REPORT_ROOT / "selected_model.json", "w", encoding="utf-8") as f:
        json.dump(selection, f, indent=2)
    # Train selected model on all development data
    selected_model = models[best_name]
    X_dev = df_dev[FEATURE_COLS]
    y_dev = df_dev[TARGET_COL]
    selected_model.fit(X_dev, y_dev)
    joblib.dump(selected_model, MODEL_DIR / "selected_development_model.joblib")
    print("Selected model", best_name, "trained on all development subjects and saved.")
    # Final test evaluation
    X_test = df_test[FEATURE_COLS]
    y_test = df_test[TARGET_COL]
    final_preds = selected_model.predict(X_test)
    final_prob = selected_model.predict_proba(X_test) if hasattr(selected_model, "predict_proba") else None
    final_acc = accuracy_score(y_test, final_preds)
    final_macro_prec = precision_score(y_test, final_preds, average="macro", zero_division=0)
    final_macro_rec = recall_score(y_test, final_preds, average="macro", zero_division=0)
    final_macro_f1 = f1_score(y_test, final_preds, average="macro", zero_division=0)
    final_wt_prec = precision_score(y_test, final_preds, average="weighted", zero_division=0)
    final_wt_rec = recall_score(y_test, final_preds, average="weighted", zero_division=0)
    final_wt_f1 = f1_score(y_test, final_preds, average="weighted", zero_division=0)
    final_report = classification_report(y_test, final_preds, output_dict=True, zero_division=0)
    final_conf = confusion_matrix(y_test, final_preds, labels=sorted(y_test.unique()))
    final_res = {"accuracy":final_acc,"macro_precision":final_macro_prec,"macro_recall":final_macro_rec,"macro_f1":final_macro_f1,"weighted_precision":final_wt_prec,"weighted_recall":final_wt_rec,"weighted_f1":final_wt_f1,"class_report":final_report,"confusion_matrix":final_conf.tolist()}
    with open(REPORT_ROOT / "final_test_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(final_res, f, indent=2)
    with open(REPORT_ROOT / "final_test_evaluation.txt", "w", encoding="utf-8") as f:
        f.write("FINAL HELD-OUT TEST (subjects 1,9,12)\n")
        f.write(f"Accuracy: {final_acc:.4f}\n")
        f.write(f"Macro Precision: {final_macro_prec:.4f}\n")
        f.write(f"Macro Recall: {final_macro_rec:.4f}\n")
        f.write(f"Macro F1: {final_macro_f1:.4f}\n")
        f.write(f"Weighted Precision: {final_wt_prec:.4f}\n")
        f.write(f"Weighted Recall: {final_wt_rec:.4f}\n")
        f.write(f"Weighted F1: {final_wt_f1:.4f}\n\n")
        f.write("Per‑class metrics:\n")
        for lbl, stats in final_report.items():
            if lbl in ["accuracy","macro avg","weighted avg"]:
                continue
            f.write(f"  {lbl}: precision {stats['precision']:.3f}, recall {stats['recall']:.3f}, f1 {stats['f1-score']:.3f}\n")
        f.write("\nConfusion Matrix (rows = true, cols = pred):\n")
        f.write(str(final_conf))
    plot_confusion(final_conf, sorted(y_test.unique()), REPORT_ROOT / "final_test_confusion.png")
    print("Final held-out test evaluation saved.")

if __name__ == "__main__":
    main()
