# PostureAI — Dataset Specification & Feature Engineering

**Document Code:** `DOC-03-DATA`  
**Relative Path:** `documents/03_DATASET_AND_FEATURE_ENGINEERING.md`  
**Primary Dataset:** MultiPosture 3D Skeletal Dataset  
**Target Feature Dimensions:** 8 Biomechanical Features  
**Target Classes:** 5 Upper-Body Posture Categories  

---

## 1. Source Dataset Overview: MultiPosture

The empirical foundation of PostureAI is derived from the **MultiPosture 3D Dataset** (`MutliPosturedataset.csv`), supplemented by the ergonomic reference dataset `dataset.csv`.

```text
+----------------------------------------------------------------------------------------------------+
|                                    RAW MULTIPOSTURE DATASET                                        |
+----------------------------------------------------------------------------------------------------+
| Total Raw Rows (including header) : 4,794 observations                                             |
| Total Columns                     : 102 features                                                   |
| Number of Human Participants      : 13 subjects (labeled 1 through 13)                             |
| Pose Estimation Backbone          : MediaPipe Pose Heavy (3D skeletal coordinates normalized to hip)|
| Metadata Columns                  : `subject`, `lowerbody_label`                                   |
| Supervised Target Column          : `upperbody_label`                                              |
| Landmark Columns                  : 33 joints x 3 dimensions (x, y, z) = 99 coordinate columns     |
+----------------------------------------------------------------------------------------------------+
```

### 1.1 Complete Landmark Indexing
The raw dataset contains 33 standardized anatomical keypoints corresponding to the BlazePose topology:
* **Head & Facial Complex (Indices 0–10):** `nose`, `left_eye_inner`, `left_eye`, `left_eye_outer`, `right_eye_inner`, `right_eye`, `right_eye_outer`, `left_ear`, `right_ear`, `mouth_left`, `mouth_right`.
* **Shoulder & Thoracic Girdle (Indices 11–12):** `left_shoulder`, `right_shoulder`.
* **Upper Extremities (Indices 13–22):** `left_elbow`, `right_elbow`, `left_wrist`, `right_wrist`, `left_pinky`, `right_pinky`, `left_index`, `right_index`, `left_thumb`, `right_thumb`.
* **Pelvic & Core Base (Indices 23–24):** `left_hip`, `right_hip`.
* **Lower Extremities (Indices 25–32):** `left_knee`, `right_knee`, `left_ankle`, `right_ankle`, `left_heel`, `right_heel`, `left_foot_index`, `right_foot_index`.

---

## 2. Dataset Validation & Quality Verification

Before feature engineering, the dataset underwent rigorous data integrity auditing (`validation_report.md`):

| Data Integrity Check | Verification Result | Operational Impact |
| :--- | :--- | :--- |
| **Missing Values (NaN / Null)** | **0 missing values** across all 102 columns | No imputation artifacts or synthetic distortions required. |
| **Infinite Values ($\pm\infty$)** | **0 infinite values** detected | Clean float64 representation across all coordinates. |
| **Duplicate Observations** | **0 duplicate rows** (excluding header) | No duplicate sample bias across experimental splits. |
| **Landmark Completeness** | All 33 3D landmarks present for all frames | Unbroken kinematic chain across all subjects. |
| **Label Integrity** | Exactly 5 valid upper-body classes | No corrupted or mislabeled target records. |

### 2.1 Coordinate Space & Physical Conventions
* **X-axis:** Lateral coronal axis (increases from subject's right to left from camera perspective).
* **Y-axis:** Vertical axial axis (negative upward in MediaPipe pixel space; inverted in feature extraction such that positive represents upward elevation).
* **Z-axis:** Sagittal depth axis (negative moves forward toward camera; positive moves backward away from camera).
* **Origin Normalization:** MediaPipe landmarks are internally normalized relative to the pelvic midpoint:
  $$\mathbf{P}_{\text{hip\_mid}} = \frac{\mathbf{P}_{\text{left\_hip}} + \mathbf{P}_{\text{right\_hip}}}{2}$$

---

## 3. Supervised Ground-Truth Posture Classes

The supervised target is `upperbody_label`, representing five distinct ergonomic trunk-spine postures:

```text
+-------+-------------------------+---------------------------------------------------------------+
| CLASS | FULL CLINICAL NAME      | BIOMECHANICAL DESCRIPTION                                     |
+-------+-------------------------+---------------------------------------------------------------+
|  TUP  | Upright Trunk           | Natural, neutral spinal alignment; minimal muscular torque;  |
|       |                         | cervical vertebrae centered over thoracic cylinder.           |
+-------+-------------------------+---------------------------------------------------------------+
|  TLF  | Trunk Leaning Forward   | Thoracic slump, spinal kyphosis, forward spinal flexion;       |
|       |                         | increased intradiscal pressure on lumbar vertebrae.           |
+-------+-------------------------+---------------------------------------------------------------+
|  TLB  | Trunk Leaning Backward  | Excessive spinal extension, posterior slump, sacral sitting;  |
|       |                         | neck hyper-extension relative to screen.                      |
+-------+-------------------------+---------------------------------------------------------------+
|  TLL  | Trunk Leaning Left      | Asymmetrical coronal left flexion; unilateral loading of left |
|       |                         | ischial tuberosity and left quadratus lumborum.               |
+-------+-------------------------+---------------------------------------------------------------+
|  TLR  | Trunk Leaning Right     | Asymmetrical coronal right flexion; unilateral loading of     |
|       |                         | right ischial tuberosity and right quadratus lumborum.        |
+-------+-------------------------+---------------------------------------------------------------+
```

> **Crucial Architectural Rule:** The 5-class upper-body label is the **ground truth for the ML model**. It is never collapsed into binary "GOOD/BAD" labels at the classifier level. `GOOD / MODERATE / BAD` is an application-level temporal risk state evaluated downstream by the `TemporalRiskEngine`.

---

## 4. The Authoritative 8 Engineered Features

To ensure fast real-time inference and prevent overfitting, the 99 raw coordinates are compressed into exactly **eight biomechanically grounded features** (`FEATURE_FUNCS` in `ml/inference/feature_extractor.py`):

```text
                    RAW 33 3D SKELETAL LANDMARKS (99 FLOATS)
                                       |
                                       v
         +-----------------------------------------------------------+
         |           MATHEMATICAL FEATURE EXTRACTION PIPELINE        |
         +-----------------------------------------------------------+
           |           |           |           |           |         |
           v           v           v           v           v         v
        head_pitch  head_roll     FHD     torso_pitch  torso_tilt  rotation
                                                           |         |
                                                           v         v
                                                      asymmetry  arm_elevation
                                       |
                                       v
                     8-DIMENSIONAL FEATURE VECTOR [F1...F8]
```

### 4.1 Feature 1: Head Pitch (`head_pitch`)
* **Definition:** Signed forward/backward inclination angle of the head relative to the shoulder midpoint in the sagittal plane.
* **Key Landmarks:** Nose (0), Left Shoulder (11), Right Shoulder (12).
* **Formula:**
  $$\mathbf{M}_{\text{shoulder}} = \frac{\mathbf{P}_{11} + \mathbf{P}_{12}}{2}$$
  $$\mathbf{V}_{\text{head}} = \mathbf{P}_{0} - \mathbf{M}_{\text{shoulder}}$$
  $$\text{head\_pitch} = \operatorname{atan2}\left(\mathbf{V}_{\text{head}}[z], -\mathbf{V}_{\text{head}}[y]\right) \times \frac{180}{\pi}$$
* **Clinical Significance:** Directly captures forward head flexion ("tech neck"). Negative values reflect downward/forward chin depression.

### 4.2 Feature 2: Head Roll (`head_roll`)
* **Definition:** Signed lateral tilt of the head in the coronal plane.
* **Key Landmarks:** Left Ear (7), Right Ear (8).
* **Formula:**
  $$\mathbf{V}_{\text{ear}} = \mathbf{P}_{8} - \mathbf{P}_{7}$$
  $$\text{head\_roll} = \operatorname{atan2}\left(\mathbf{V}_{\text{ear}}[y], \mathbf{V}_{\text{ear}}[x]\right) \times \frac{180}{\pi}$$
* **Clinical Significance:** Measures head tilting toward the left or right shoulder, common when cradling phones or looking at offset monitors.

### 4.3 Feature 3: Forward Head Displacement (`forward_head_displacement` / FHD)
* **Definition:** Normalized horizontal forward translation of the head relative to the torso length.
* **Key Landmarks:** Nose (0), Shoulders (11, 12), Hips (23, 24).
* **Formula:**
  $$\mathbf{M}_{\text{hip}} = \frac{\mathbf{P}_{23} + \mathbf{P}_{24}}{2}$$
  $$L_{\text{torso}} = \|\mathbf{M}_{\text{shoulder}} - \mathbf{M}_{\text{hip}}\|$$
  $$\mathbf{u}_{\text{fwd}} = \begin{bmatrix} 0 & 0 & -1 \end{bmatrix}^T$$
  $$\text{FHD} = \frac{(\mathbf{P}_{0} - \mathbf{M}_{\text{shoulder}}) \cdot \mathbf{u}_{\text{fwd}}}{L_{\text{torso}}}$$
* **Clinical Significance:** Unlike pure angles, FHD provides a scale-invariant metric of forward head translation normalized to the user's bodily dimensions.

### 4.4 Feature 4: Torso Pitch (`torso_pitch`)
* **Definition:** Signed forward/backward inclination angle of the trunk vector relative to vertical.
* **Key Landmarks:** Shoulders (11, 12), Hips (23, 24).
* **Formula:**
  $$\mathbf{V}_{\text{torso}} = \mathbf{M}_{\text{shoulder}} - \mathbf{M}_{\text{hip}}$$
  $$\text{torso\_pitch} = \operatorname{atan2}\left(\mathbf{V}_{\text{torso}}[z], -\mathbf{V}_{\text{torso}}[y]\right) \times \frac{180}{\pi}$$
* **Clinical Significance:** Primary discriminator for spinal slouching (`TLF`) vs reclined sitting (`TLB`) vs neutral upright posture (`TUP`).

### 4.5 Feature 5: Torso Lateral Tilt (`torso_lateral_tilt`)
* **Definition:** Signed coronal side-bending of the trunk relative to horizontal.
* **Formula:**
  $$\text{torso\_lateral\_tilt} = \operatorname{atan2}\left(\mathbf{V}_{\text{torso}}[y], \mathbf{V}_{\text{torso}}[x]\right) \times \frac{180}{\pi}$$
* **Clinical Significance:** Quantifies asymmetric lateral spinal leaning (`TLL` vs `TLR`).

### 4.6 Feature 6: Torso Axial Rotation (`torso_rotation`)
* **Definition:** Estimated rotational twist of the shoulders relative to the pelvic axis in the transverse plane.
* **Formula:**
  $$\mathbf{A}_{\text{shoulder}} = \begin{bmatrix} \mathbf{P}_{12}[x] - \mathbf{P}_{11}[x] & \mathbf{P}_{12}[z] - \mathbf{P}_{11}[z] \end{bmatrix}$$
  $$\mathbf{A}_{\text{hip}} = \begin{bmatrix} \mathbf{P}_{24}[x] - \mathbf{P}_{23}[x] & \mathbf{P}_{24}[z] - \mathbf{P}_{23}[z] \end{bmatrix}$$
  $$\theta_{\text{shoulder}} = \operatorname{atan2}(\mathbf{A}_{\text{shoulder}}[1], \mathbf{A}_{\text{shoulder}}[0]) \times \frac{180}{\pi}$$
  $$\theta_{\text{hip}} = \operatorname{atan2}(\mathbf{A}_{\text{hip}}[1], \mathbf{A}_{\text{hip}}[0]) \times \frac{180}{\pi}$$
  $$\text{torso\_rotation} = \theta_{\text{shoulder}} - \theta_{\text{hip}}$$
* **Clinical Significance:** Captures rotational spinal torque resulting from twisting toward secondary monitors or off-axis keyboards.

### 4.7 Feature 7: Shoulder Asymmetry (`shoulder_asymmetry`)
* **Definition:** Normalized vertical height imbalance between left and right acromioclavicular joints.
* **Formula:**
  $$W_{\text{shoulder}} = \|\mathbf{P}_{12} - \mathbf{P}_{11}\|$$
  $$\text{shoulder\_asymmetry} = \frac{|\mathbf{P}_{11}[y] - \mathbf{P}_{12}[y]|}{W_{\text{shoulder}}}$$
* **Clinical Significance:** High asymmetry flags single-elbow resting, uneven armrests, or habitual shoulder hiking.

### 4.8 Feature 8: Upper Arm Elevation (`upper_arm_elevation`)
* **Definition:** Mean elevation angle of the left and right humerus relative to the torso axis.
* **Key Landmarks:** Shoulders (11, 12), Elbows (13, 14).
* **Formula:**
  $$\mathbf{V}_{\text{left\_arm}} = \mathbf{P}_{13} - \mathbf{P}_{11}, \quad \mathbf{V}_{\text{right\_arm}} = \mathbf{P}_{14} - \mathbf{P}_{12}$$
  $$\phi_{\text{left}} = \operatorname{atan2}\left(\sqrt{\mathbf{V}_{\text{left}}[x]^2 + \mathbf{V}_{\text{left}}[z]^2}, -\mathbf{V}_{\text{left}}[y]\right) \times \frac{180}{\pi}$$
  $$\phi_{\text{right}} = \operatorname{atan2}\left(\sqrt{\mathbf{V}_{\text{right}}[x]^2 + \mathbf{V}_{\text{right}}[z]^2}, -\mathbf{V}_{\text{right}}[y]\right) \times \frac{180}{\pi}$$
  $$\text{upper\_arm\_elevation} = \frac{\phi_{\text{left}} + \phi_{\text{right}}}{2}$$
* **Clinical Significance:** Aligns with standard RULA ergonomic assessment criteria for shoulder abduction and reaching strain.

---

## 5. Extended Ergonomic Feature Suite

In addition to the 8 core classification features, PostureAI includes an extended suite (`EXTENDED_FEATURE_FUNCS` in `generate_enriched_dataset.py`) for specialized clinical reports:

| Feature Name | Primary Formulation | Ergonomic Purpose |
| :--- | :--- | :--- |
| **Craniovertebral Angle (CVA)** | Angle of line from C7 (mid-shoulder) to tragus (mid-ear) relative to horizontal. | Gold-standard clinical benchmark for forward head posture; CVA $< 50^\circ$ indicates clinical forward head deformity. |
| **Neck Lateral Tilt** | Coronal tilt of ear-shoulder vector relative to vertical: $\operatorname{atan2}(V_{\text{neck}}[x], -V_{\text{neck}}[y])$. | Isolate cervical spine lateral flexion from thoracic spine lateral tilt. |
| **Shoulder Tilt Angle** | Absolute angle of inter-shoulder line: $\operatorname{atan2}(\Delta y, \Delta x)$. | Measures pure coronal plane shoulder slope. |
| **Spine Lateral Deviation** | Orthogonal distance of thoracic midpoint from pelvic-cervical midline. | Detects scoliosis-like compensatory spinal curves. |

---

## 6. Feature Correlation & Statistical Summary

Summary statistics computed across the 4,794 MultiPosture samples (`feature_statistics.csv`):

| Feature Name | Mean | Std Dev | Min | Median | Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `head_pitch` | $-33.42^\circ$ | $14.28^\circ$ | $-78.50^\circ$ | $-32.10^\circ$ | $+18.40^\circ$ |
| `head_roll` | $-0.85^\circ$ | $9.64^\circ$ | $-44.20^\circ$ | $-0.40^\circ$ | $+42.80^\circ$ |
| `forward_head_displacement` | $0.284$ | $0.112$ | $-0.082$ | $0.276$ | $0.694$ |
| `torso_pitch` | $-22.18^\circ$ | $12.85^\circ$ | $-62.40^\circ$ | $-21.90^\circ$ | $+24.60^\circ$ |
| `torso_lateral_tilt` | $-89.42^\circ$ | $8.74^\circ$ | $-128.50^\circ$ | $-89.60^\circ$ | $-52.10^\circ$ |
| `torso_rotation` | $+1.45^\circ$ | $11.32^\circ$ | $-38.90^\circ$ | $+0.80^\circ$ | $+41.20^\circ$ |
| `shoulder_asymmetry` | $0.078$ | $0.054$ | $0.001$ | $0.065$ | $0.384$ |
| `upper_arm_elevation` | $28.60^\circ$ | $9.45^\circ$ | $+8.20^\circ$ | $27.40^\circ$ | $+72.30^\circ$ |

### 6.1 Key Insights from Correlation Analysis
* **Torso Pitch vs Forward Head Displacement ($r = 0.72$):** Strong positive correlation between trunk slouching and forward head translation. As desk workers slump forward, the head mechanically projects outward to maintain horizontal gaze at the monitor.
* **Torso Lateral Tilt vs Head Roll ($r = 0.58$):** Lateral leaning of the torso is coupled with lateral head tilting, demonstrating whole-spine compensatory mechanics during asymmetrical sitting.
* **Shoulder Asymmetry vs Torso Rotation ($r = 0.34$):** Coronal shoulder imbalance is moderately correlated with axial twist, consistent with single-armrest leaning.
