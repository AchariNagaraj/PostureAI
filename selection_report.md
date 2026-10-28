# Model Comparison & Selection Report

**Selected Model:** `RandomForest`

**Why this model?**
- It achieved the **highest mean Macro F1** score among all evaluated models.
- If there were ties, the selection rule would use the **highest weighted F1** as the tie‑breaker.

## Overall Performance (Development Cross‑Validation)
| Metric | Mean | Std |
|--------|------|-----|
| Accuracy | 0.9861 | 0.0164 |
| Macro Precision | 0.9750 | 0.0281 |
| Macro Recall | 0.9880 | 0.0087 |
| **Macro F1** | **0.9797** | 0.0205 |
| Weighted Precision | 0.9891 | 0.0115 |
| Weighted Recall | 0.9861 | 0.0164 |
| **Weighted F1** | **0.9867** | 0.0153 |

## Per‑Class Metrics (Cross‑Validation Averages)
| Class | Precision (mean) | Recall (mean) | F1 (mean) |
|-------|------------------|--------------|----------|
| TLB | 0.960 | 0.691 | 0.802 |
| TLF | 0.949 | 0.989 | 0.969 |
| TLL | 1.000 | 0.933 | 0.966 |
| TLR | 1.000 | 0.767 | 0.868 |
| TUP | 0.844 | 0.996 | 0.914 |

*(Values are rounded to three decimals for readability.)*

## Test Set Evaluation (Held‑out subjects 1, 9, 12)
The final model was trained on **all development subjects** (2, 3, 4, 5, 6, 7, 8, 10, 11, 13) and evaluated on the untouched test subjects.

- **Accuracy:** `0.9769`
- **Macro Precision:** `0.9832`
- **Macro Recall:** `0.9605`
- **Macro F1:** `0.9695`
- **Weighted Precision:** `0.9784`
- **Weighted Recall:** `0.9769`
- **Weighted F1:** `0.9761`

### Per‑Class Test Metrics
- **TLB:** precision 0.994, recall 1.000, f1 0.997
- **TLF:** precision 0.925, recall 0.996, f1 0.959
- **TLL:** precision 1.000, recall 0.808, f1 0.894
- **TLR:** precision 1.000, recall 1.000, f1 1.000
- **TUP:** precision 0.998, recall 0.998, f1 0.998

### Confusion Matrix (rows = true, cols = pred)
```
[[154   0   0   0   0]
 [  0 284   0   0   1]
 [  0  23  97   0   0]
 [  0   0   0 120   0]
 [  1   0   0   0 400]]
```

The detailed JSON report can be found at [final_test_evaluation.json](file:///d:/FinalYearProject/reports/ml/model_comparison/final_test_evaluation.json).

## Reproducibility Details
- **Random seed:** 42
- **Feature columns:** head_pitch, head_roll, forward_head_displacement, torso_pitch, torso_lateral_tilt, torso_rotation, shoulder_asymmetry, upper_arm_elevation
- **Target column:** `upperbody_label`
- **Development subjects:** 2, 3, 4, 5, 6, 7, 8, 10, 11, 13
- **Final test subjects:** 1, 9, 12

The trained model artifact is saved as:
```
models/selected_development_model.joblib
```

*All decisions respect the project constraints: a single dataset, single feature pipeline, and a unified posture model.*
