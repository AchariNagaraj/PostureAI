#!/usr/bin/env python
"""generate_enriched_dataset.py

Generates an enriched posture dataset combining real 3D skeletal data from MultiPosture
with ergonomic head and shoulder features inspired by `dataset.csv`.

Features:
- Head/Neck: head_pitch, head_roll, forward_head_displacement, forward_head_distance,
             craniovertebral_angle (CVA), neck_lateral_tilt, neck_deviation
- Shoulder/Arm: shoulder_diff, shoulder_asymmetry, shoulder_tilt_angle,
                shoulder_protraction_asym, upper_arm_elevation
- Torso/Spine: torso_pitch, torso_lateral_tilt, torso_rotation, spine_lateral_deviation
- Dual Targets: upperbody_label (TUP, TLB, TLF, TLR, TLL) & risk_label (GOOD, MODERATE, BAD)
"""

import os
import sys
import argparse
import pathlib
import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(description="Generate enriched posture dataset.")
    parser.add_argument(
        "--raw-data",
        type=str,
        default="ml/preprocessing/MutliPosturedataset.csv",
        help="Path to raw MultiPosture CSV file.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/posture_extended_dataset.csv",
        help="Output path for enriched CSV dataset.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="reports/ml",
        help="Directory to store dataset summary report.",
    )
    return parser.parse_args()


def extract_features_from_row(r: pd.Series) -> dict:
    """Extract full suite of head, shoulder, torso features and risk state from landmark coordinates."""
    # Key landmark coordinates
    nose = np.array([r["nose_x"], r["nose_y"], r["nose_z"]], dtype=np.float64)
    le = np.array([r["left_ear_x"], r["left_ear_y"], r["left_ear_z"]], dtype=np.float64)
    re = np.array([r["right_ear_x"], r["right_ear_y"], r["right_ear_z"]], dtype=np.float64)
    ls = np.array([r["left_shoulder_x"], r["left_shoulder_y"], r["left_shoulder_z"]], dtype=np.float64)
    rs = np.array([r["right_shoulder_x"], r["right_shoulder_y"], r["right_shoulder_z"]], dtype=np.float64)
    lh = np.array([r["left_hip_x"], r["left_hip_y"], r["left_hip_z"]], dtype=np.float64)
    rh = np.array([r["right_hip_x"], r["right_hip_y"], r["right_hip_z"]], dtype=np.float64)
    lelb = np.array([r["left_elbow_x"], r["left_elbow_y"], r["left_elbow_z"]], dtype=np.float64)
    relb = np.array([r["right_elbow_x"], r["right_elbow_y"], r["right_elbow_z"]], dtype=np.float64)

    # Midpoints & reference lengths
    ms = (ls + rs) / 2.0
    mh = (lh + rh) / 2.0
    me = (le + re) / 2.0
    torso_vec = ms - mh
    torso_len = float(np.linalg.norm(torso_vec))
    shoulder_width = float(np.linalg.norm(rs - ls))
    if torso_len < 1e-5:
        torso_len = 1.0
    if shoulder_width < 1e-5:
        shoulder_width = 1.0

    # -------------------------------------------------------------
    # 1. Head & Neck Features (Inspired by dataset.csv + Ergonomics)
    # -------------------------------------------------------------
    # 1.1 head_pitch: Sagittal forward/backward head angle (degrees)
    # Nose relative to mid-shoulder: Y is negative upward, Z is forward out of screen
    head_vec = nose - ms
    head_pitch = float(np.degrees(np.arctan2(head_vec[2], -head_vec[1])))

    # 1.2 head_roll: Lateral head roll from ears (degrees)
    ear_vec = re - le
    head_roll = float(np.degrees(np.arctan2(ear_vec[1], ear_vec[0])))

    # 1.3 forward_head_displacement: Normalized forward translation ratio
    forward_axis = np.array([0.0, 0.0, -1.0])
    forward_disp = float(np.dot(head_vec, forward_axis))
    forward_head_displacement = forward_disp / torso_len

    # 1.4 forward_head_distance: Direct raw forward distance (inspired by dataset.csv 'forward_head')
    forward_head_distance = float(-head_vec[2])

    # 1.5 craniovertebral_angle (CVA): Gold standard clinical ergonomic metric for forward head posture
    # Angle in sagittal plane between horizontal axis and line connecting mid-shoulder (C7 proxy) and mid-ear (tragus proxy)
    neck_vec = me - ms
    # Horizontal axis is parallel to Z; vertical is -Y.
    cva = float(np.degrees(np.arctan2(-neck_vec[1], abs(neck_vec[2]) + 1e-5)))

    # 1.6 neck_lateral_tilt: Coronal lateral angle of neck vector relative to vertical (inspired by dataset.csv 'neck_side')
    neck_lateral_tilt = float(np.degrees(np.arctan2(neck_vec[0], -neck_vec[1] + 1e-5)))

    # 1.7 neck_deviation: 3D angular deviation of neck vector from upright vertical (inspired by dataset.csv 'neck_dev')
    vertical_axis = np.array([0.0, -1.0, 0.0])
    neck_norm = float(np.linalg.norm(neck_vec))
    if neck_norm > 1e-5:
        cos_neck = float(np.dot(neck_vec, vertical_axis) / neck_norm)
        cos_neck = np.clip(cos_neck, -1.0, 1.0)
        neck_deviation = float(np.degrees(np.arccos(cos_neck)))
    else:
        neck_deviation = 0.0

    # -------------------------------------------------------------
    # 2. Shoulder & Arm Features (Inspired by dataset.csv 'shoulder_diff')
    # -------------------------------------------------------------
    # 2.1 shoulder_diff: Raw vertical height difference between left and right shoulders (MediaPipe Y)
    shoulder_diff = float(abs(ls[1] - rs[1]))

    # 2.2 shoulder_asymmetry: Normalized shoulder height imbalance
    shoulder_asymmetry = shoulder_diff / shoulder_width

    # 2.3 shoulder_tilt_angle: Coronal angle of shoulder axis line relative to horizontal
    shoulder_tilt_angle = float(np.degrees(np.arctan2(rs[1] - ls[1], rs[0] - ls[0])))

    # 2.4 shoulder_protraction_asym: Z-depth difference between shoulders (sagittal asymmetry / rounding)
    shoulder_protraction_asym = float(abs(ls[2] - rs[2]))

    # 2.5 upper_arm_elevation: Bilateral mean upper arm angle relative to downward torso
    vec_l = lelb - ls
    vec_r = relb - rs
    el_l = float(np.degrees(np.arctan2(np.sqrt(vec_l[0]**2 + vec_l[2]**2), -vec_l[1])))
    el_r = float(np.degrees(np.arctan2(np.sqrt(vec_r[0]**2 + vec_r[2]**2), -vec_r[1])))
    upper_arm_elevation = float((el_l + el_r) / 2.0)

    # -------------------------------------------------------------
    # 3. Torso & Spine Features (Inspired by dataset.csv 'spine_forward', 'spine_side', 'spine_dev')
    # -------------------------------------------------------------
    # 3.1 torso_pitch: Sagittal forward/backward trunk inclination
    torso_pitch = float(np.degrees(np.arctan2(torso_vec[2], -torso_vec[1])))

    # 3.2 torso_lateral_tilt: Coronal left/right trunk inclination
    torso_lateral_tilt = float(np.degrees(np.arctan2(torso_vec[1], torso_vec[0])))

    # 3.3 torso_rotation: Axial trunk rotation (yaw difference shoulder vs hip)
    s_axis = rs[[0, 2]] - ls[[0, 2]]
    h_axis = rh[[0, 2]] - lh[[0, 2]]
    yaw_s = np.degrees(np.arctan2(s_axis[1], s_axis[0]))
    yaw_h = np.degrees(np.arctan2(h_axis[1], h_axis[0]))
    torso_rotation = float(yaw_s - yaw_h)

    # 3.4 spine_lateral_deviation: Lateral deviation of spine from neutral vertical (-90 deg)
    spine_lateral_deviation = float(min(abs(torso_lateral_tilt + 90.0), abs(torso_lateral_tilt - 90.0)))

    # -------------------------------------------------------------
    # 4. Target Labels (Dual: MultiPosture Class & Risk State)
    # -------------------------------------------------------------
    upper_label = str(r["upperbody_label"])
    lower_label = str(r.get("lowerbody_label", ""))

    # Clinical & Ergonomic Risk Mapping (GOOD, MODERATE, BAD):
    # - TUP (Trunk Upright) represents baseline neutral sitting.
    #   If slight tilt is observed -> MODERATE. Otherwise -> GOOD.
    # - Non-upright postures (TLF, TLB, TLR, TLL):
    #   Moderate flexion/tilt -> MODERATE.
    #   Severe flexion (|tp| > 25° or spine_dev > 25° or CVA < 18°) -> BAD.
    if upper_label == "TUP":
        if abs(torso_pitch) > 10.0 or abs(neck_lateral_tilt) > 18.0 or shoulder_asymmetry > 0.22:
            risk_label = "MODERATE"
        else:
            risk_label = "GOOD"
    else:
        if abs(torso_pitch) > 25.0 or spine_lateral_deviation > 25.0 or cva < 18.0:
            risk_label = "BAD"
        else:
            risk_label = "MODERATE"

    return {
        "subject": int(r["subject"]),
        "upperbody_label": upper_label,
        "lowerbody_label": lower_label,
        "risk_label": risk_label,
        # Head / Neck Features
        "head_pitch": head_pitch,
        "head_roll": head_roll,
        "forward_head_displacement": forward_head_displacement,
        "forward_head_distance": forward_head_distance,
        "craniovertebral_angle": cva,
        "neck_lateral_tilt": neck_lateral_tilt,
        "neck_deviation": neck_deviation,
        # Shoulder / Arm Features
        "shoulder_diff": shoulder_diff,
        "shoulder_asymmetry": shoulder_asymmetry,
        "shoulder_tilt_angle": shoulder_tilt_angle,
        "shoulder_protraction_asym": shoulder_protraction_asym,
        "upper_arm_elevation": upper_arm_elevation,
        # Torso / Spine Features
        "torso_pitch": torso_pitch,
        "torso_lateral_tilt": torso_lateral_tilt,
        "torso_rotation": torso_rotation,
        "spine_lateral_deviation": spine_lateral_deviation,
    }


def generate_dataset(raw_path: str, output_path: str, report_dir: str):
    print(f"Loading raw dataset from {raw_path}...")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Input file not found: {raw_path}")

    raw_df = pd.read_csv(raw_path)
    print(f"Loaded {len(raw_df)} raw samples with {raw_df.shape[1]} columns.")

    print("Extracting enriched features (head, neck, shoulder, arm, torso)...")
    records = []
    for idx, row in raw_df.iterrows():
        rec = extract_features_from_row(row)
        records.append(rec)

    enriched_df = pd.DataFrame(records)

    # Data validation: check for NaNs or Infs
    null_counts = enriched_df.isna().sum()
    if null_counts.sum() > 0:
        print("Warning: Missing values found:")
        print(null_counts[null_counts > 0])
        enriched_df = enriched_df.dropna().reset_index(drop=True)

    # Save dataset
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    enriched_df.to_csv(output_path, index=False)
    print(f"Saved enriched dataset to {output_path} ({len(enriched_df)} rows, {enriched_df.shape[1]} columns).")

    # Generate summary report
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, "enriched_dataset_report.md")
    
    summary_stats = enriched_df.describe().T
    class_dist = enriched_df["upperbody_label"].value_counts()
    risk_dist = enriched_df["risk_label"].value_counts()
    cross_tab = pd.crosstab(enriched_df["upperbody_label"], enriched_df["risk_label"])

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# PostureAI Enriched Dataset Report\n\n")
        f.write("## Overview\n")
        f.write(f"- **Total Samples:** {len(enriched_df)}\n")
        f.write(f"- **Total Features & Metadata:** {enriched_df.shape[1]}\n")
        f.write(f"- **Subjects:** {sorted(enriched_df['subject'].unique().tolist())}\n")
        f.write(f"- **Primary Target 1 (Posture Class):** TUP, TLB, TLF, TLR, TLL\n")
        f.write(f"- **Primary Target 2 (Ergonomic Risk):** GOOD, MODERATE, BAD\n\n")

        f.write("## Posture Class Distribution\n")
        f.write("| Posture Class | Count | Percentage |\n|---|---|---|\n")
        for cls, count in class_dist.items():
            pct = count / len(enriched_df) * 100.0
            f.write(f"| {cls} | {count} | {pct:.1f}% |\n")
        f.write("\n")

        f.write("## Ergonomic Risk Level Distribution\n")
        f.write("| Risk Level | Count | Percentage |\n|---|---|---|\n")
        for risk, count in risk_dist.items():
            pct = count / len(enriched_df) * 100.0
            f.write(f"| {risk} | {count} | {pct:.1f}% |\n")
        f.write("\n")

        f.write("## Posture Class vs. Risk Level Mapping\n")
        f.write(cross_tab.to_markdown())
        f.write("\n\n")

        f.write("## Feature Summary Statistics\n")
        f.write(summary_stats[["mean", "std", "min", "50%", "max"]].to_markdown())
        f.write("\n")

    print(f"Generated summary report at {report_file}")
    return enriched_df


if __name__ == "__main__":
    args = parse_args()
    generate_dataset(args.raw_data, args.output_csv, args.report_dir)
