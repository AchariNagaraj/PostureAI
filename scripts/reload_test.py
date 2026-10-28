#!/usr/bin/env python
"""reload_test.py
Verification that the saved RandomForest model can be loaded and used for inference on held‑out test samples.
"""

import pathlib
import pandas as pd
import joblib
from sklearn.model_selection import GroupShuffleSplit

# Paths
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "multiposture_engineered.csv"
MODEL_PATH = pathlib.Path(__file__).resolve().parents[1] / "ml" / "models" / "posture_model.joblib"

# Feature / target columns (must match training script)
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

# Load data
df = pd.read_csv(DATA_PATH)

# Re‑create the same subject‑wise split (seed 42, 70/15/15)
SEED = 42
TRAIN_SIZE = 0.70
VAL_SIZE = 0.15

gss = GroupShuffleSplit(n_splits=1, train_size=TRAIN_SIZE, random_state=SEED)
train_idx, temp_idx = next(gss.split(df, groups=df["subject"]))
temp_df = df.iloc[temp_idx]
val_frac = VAL_SIZE / (1 - TRAIN_SIZE)

gss2 = GroupShuffleSplit(n_splits=1, train_size=val_frac, random_state=SEED)
val_idx, test_idx = next(gss2.split(temp_df, groups=temp_df["subject"]))

test_df = temp_df.iloc[test_idx]
X_test = test_df[FEATURE_COLS]

# Load model
model = joblib.load(MODEL_PATH)

# Predict on first five test rows (or all if fewer)
sample_X = X_test.head(5)
pred = model.predict(sample_X)
proba = model.predict_proba(sample_X)

print("Loaded model from", MODEL_PATH)
print("Number of test samples:", len(X_test))
print("Sample predictions (first up to 5 rows):", pred.tolist())
print("Prediction probabilities shape:", proba.shape)
