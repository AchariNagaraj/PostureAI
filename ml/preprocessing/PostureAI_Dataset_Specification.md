# PostureAI — Dataset Design & Feature Engineering Specification

## 1. Purpose

This document is the single source of truth for the PostureAI dataset pipeline, covering:

- raw MultiPosture data
- labels
- preprocessing
- landmark selection
- coordinate conventions
- feature engineering
- the final eight engineered features
- dataset splitting
- model-ready data
- training/deployment consistency
- GOOD/MODERATE/BAD risk interpretation
- research/report methodology

> **Core decision:** MultiPosture's original upper-body labels remain the supervised ML ground truth. `GOOD / MODERATE / BAD` is an application-level temporal risk state and is **not** an invented relabeling of the source dataset.

---

# 2. Overall Dataset Pipeline

```text
                  MULTIPOSTURE RAW DATA
                          |
                          v
                 Data Validation
                          |
                          v
                Landmark Selection
                          |
                          v
              Coordinate Processing
                          |
                          v
              Feature Engineering
                          |
                          v
                8 Engineered Features
                          |
                          v
              Subject-wise Data Split
                          |
                          v
                 Random Forest
                          |
                          v
              TUP / TLB / TLF / TLR / TLL
                          |
                 +--------+--------+
                 |                 |
                 v                 v
          Model Confidence   Personal Baseline
                 |                 |
                 +--------+--------+
                          |
                          v
                Temporal Risk Engine
                          |
                          v
                GOOD / MODERATE / BAD
                          |
                          v
                Alert / Recommendation
```

---

# 3. Source Dataset: MultiPosture

The uploaded MultiPosture CSV contains:

- `subject`
- `upperbody_label`
- `lowerbody_label`
- MediaPipe-derived landmark coordinates
- x, y and z values for the available landmarks

The actual uploaded header contains head landmarks (nose, eyes, ears, mouth), shoulders, elbows, wrists/hand landmarks, hips, knees, ankles, heels and foot-index landmarks.

Source: the uploaded `Pasted markdown(1).md` dataset.

---

# 4. Raw Dataset Structure

Conceptually:

```text
+------------------------------------------------------+
|                   RAW MULTIPOSTURE                  |
+------------------------------------------------------+
| Metadata                                             |
|   subject                                            |
|                                                      |
| Ground-truth labels                                  |
|   upperbody_label                                    |
|   lowerbody_label                                    |
|                                                      |
| Head landmarks                                       |
|   nose                                               |
|   left/right eyes                                    |
|   left/right ears                                    |
|   left/right mouth                                   |
|                                                      |
| Upper-body landmarks                                 |
|   left/right shoulder                               |
|   left/right elbow                                  |
|   left/right wrist                                  |
|   hand landmarks                                    |
|                                                      |
| Lower-body landmarks                                 |
|   left/right hip                                    |
|   left/right knee                                   |
|   left/right ankle                                  |
|   left/right heel                                   |
|   left/right foot index                             |
+------------------------------------------------------+
```

Each landmark is represented using:

```text
landmark_x
landmark_y
landmark_z
```

For example:

```text
left_shoulder_x
left_shoulder_y
left_shoulder_z

right_shoulder_x
right_shoulder_y
right_shoulder_z
```

---

# 5. Metadata and Labels

## 5.1 `subject`

`subject` identifies the participant.

Use it for:

- subject-wise train/validation/test splitting
- leakage prevention
- participant-level evaluation

Do **not** pass it to the classifier.

```text
subject
   |
   +--> splitting/evaluation
   |
   X--> ML input
```

## 5.2 Upper-body labels

The main supervised target is:

| Label | Meaning |
|---|---|
| `TUP` | Trunk Upright Position |
| `TLB` | Trunk Leaning Backward |
| `TLF` | Trunk Leaning Forward |
| `TLR` | Trunk Leaning Right |
| `TLL` | Trunk Leaning Left |

Thus:

```text
8 engineered features
        |
        v
TUP / TLB / TLF / TLR / TLL
```

## 5.3 Lower-body labels

The raw dataset also contains lower-body labels including:

```text
LAP
LWA
LCS
LCR
LCL
LLR
LLL
```

Retain these for metadata and future experiments, but do not use them as the primary target for the current upper-body sitting-posture classifier.

---

# 6. Why We Do Not Convert the Source Labels to GOOD/MODERATE/BAD

Do not arbitrarily create:

```text
TUP -> GOOD
TLF -> BAD
TLB -> BAD
TLR -> MODERATE
TLL -> MODERATE
```

That would create artificial ground truth.

A posture class does not by itself constitute a complete ergonomic or medical risk assessment. Established ergonomic approaches consider additional variables such as body-region angles, loading, muscle use and duration.

Therefore:

```text
SOURCE GROUND TRUTH
TUP/TLB/TLF/TLR/TLL
          |
          v
   ML POSTURE MODEL
          |
          v
confidence + baseline + temporal persistence
          |
          v
PostureAI application risk state
GOOD/MODERATE/BAD
```

---

# 7. Data Cleaning and Validation

Before feature engineering:

### Missing values

Check all required coordinates for:

```text
NaN
null
inf
-inf
```

### Invalid labels

Verify:

```text
upperbody_label ∈
{TUP, TLB, TLF, TLR, TLL}
```

### Duplicates

Check duplicate rows and investigate them before removal. Sequential frames can legitimately be similar.

### Landmark availability

Every feature must verify that its required landmarks exist and are valid.

If required landmarks are unavailable, the observation should be marked invalid/insufficient rather than assigned a false posture label.

---

# 8. Anatomical Feature Structure

The final features are deliberately grouped into three body regions:

```text
                  POSTURE FEATURES
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
    HEAD/NECK        SHOULDERS/ARMS      TORSO
        |                |                |
   +----+----+       +---+----+       +---+---+---+
   |    |    |       |        |       |   |   |   |
 Pitch Roll  FHD   Shoulder   Arm    Pitch Tilt Rotation
                Asymmetry   Elev.
```

Total = **8 engineered features**.

---

# 9. Final Eight Features

| # | Feature | Region | Type | Purpose |
|---|---|---|---|---|
| 1 | `head_pitch` | Head/neck | Signed angle | Forward/backward head inclination |
| 2 | `head_roll` | Head/neck | Signed angle | Left/right head inclination |
| 3 | `forward_head_displacement` | Head/neck | Normalized distance | Forward head position relative to torso |
| 4 | `torso_pitch` | Torso | Signed angle | Forward/backward trunk inclination |
| 5 | `torso_lateral_tilt` | Torso | Signed angle | Left/right trunk inclination |
| 6 | `torso_rotation` | Torso | Relative angle | Axial trunk rotation |
| 7 | `shoulder_asymmetry` | Shoulders | Normalized difference | Left/right shoulder imbalance |
| 8 | `upper_arm_elevation` | Shoulders/arms | Angle | Upper-arm elevation |

---

# 10. Feature 1 — `head_pitch`

## Meaning

Forward/backward inclination of the head.

Conceptually:

```text
             HEAD
              O
             /
            /
        neck reference
              |
              |
            torso
```

A stable head/neck reference should be constructed from the available head landmarks rather than relying on one arbitrary point.

Conceptually:

```text
head_pitch =
    signed_angle(head_reference, reference_axis)
```

It must remain **signed** so forward and backward inclination are distinguishable.

Do not replace it with:

```python
abs(head_pitch)
```

because that removes directional information.

## Limitation

Do not automatically interpret a particular angle as a medical `BAD` threshold.

---

# 11. Feature 2 — `head_roll`

## Meaning

Lateral head inclination.

```text
Neutral:

       O
       |
       |

Tilt:

        O
       /
      /
```

Conceptually:

```text
head_roll =
    signed_lateral_angle(head_reference)
```

The raw dataset provides multiple head landmarks, including eyes and ears, which can be used to construct a stable head orientation.

---

# 12. Feature 3 — `forward_head_displacement`

Head angle and head translation are different.

Example:

```text
             HEAD
              O
              |
              |  forward displacement
              |
         shoulder reference
              |
              |
             hip
```

A normalized feature is preferred:

```text
forward_head_displacement =
    head_forward_offset / torso_length
```

with:

```text
shoulder_center =
    (left_shoulder + right_shoulder) / 2

hip_center =
    (left_hip + right_hip) / 2

torso_length =
    distance(shoulder_center, hip_center)
```

The exact projection used for `head_forward_offset` must be fixed with the camera/coordinate convention.

This is an ML feature, not a universal medical threshold.

---

# 13. Feature 4 — `torso_pitch`

## Meaning

Forward/backward trunk inclination.

First:

```text
shoulder_center =
    (left_shoulder + right_shoulder) / 2

hip_center =
    (left_hip + right_hip) / 2
```

Then:

```text
torso_vector =
    shoulder_center - hip_center
```

and:

```text
torso_pitch =
    signed_angle(torso_vector, reference_axis)
```

Conceptually:

```text
      shoulder center
             O
            /
           /
          /
       hip center
```

This feature is particularly important for separating:

```text
TUP
TLF
TLB
```

---

# 14. Feature 5 — `torso_lateral_tilt`

## Meaning

Left/right trunk inclination.

```text
Upright:

    shoulder
       |
       |
      hip


Lateral tilt:

     shoulder
                           hip
```

Conceptually:

```text
torso_lateral_tilt =
    signed_lateral_angle(torso_vector)
```

This contributes information for:

```text
TLL
TLR
```

---

# 15. Feature 6 — `torso_rotation`

## Meaning

Forward/backward pitch does not capture twisting.

Use the shoulder and hip axes:

```text
Shoulder axis:

left shoulder -------- right shoulder

Hip axis:

left hip ------------- right hip
```

Then estimate their relative orientation:

```text
torso_rotation =
    relative_orientation(shoulder_axis, hip_axis)
```

Conceptually:

```text
Shoulder axis
      /
     /
    /   rotation
   ↻
  /
Hip axis
```

Because this is derived from MediaPipe-estimated 3D pose, report it as **estimated torso rotation**, not clinically measured spinal rotation.

---

# 16. Feature 7 — `shoulder_asymmetry`

## Meaning

Left/right shoulder imbalance.

Conceptually:

```text
Symmetric:

L shoulder -------- R shoulder
       same level


Asymmetric:

L shoulder
             \-------- R shoulder
```

One normalized formulation:

```text
shoulder_height_difference =
    abs(left_shoulder_vertical -
        right_shoulder_vertical)

shoulder_width =
    distance(left_shoulder, right_shoulder)

shoulder_asymmetry =
    shoulder_height_difference / shoulder_width
```

This is a model feature.

Do not claim a universal medical threshold such as:

```text
shoulder_asymmetry > X = BAD
```

without external validation.

---

# 17. Feature 8 — `upper_arm_elevation`

## Meaning

Upper-arm position relative to the torso/reference axis.

For each arm:

```text
upper_arm_vector =
    elbow - shoulder
```

Then calculate the elevation angle.

Conceptually:

```text
      shoulder
          O
         /
        /
       elbow
```

For the current eight-feature design, a single bilateral feature is used. If both arms are available, the aggregation rule must be frozen before training, for example:

```text
upper_arm_elevation =
    mean(left_arm_elevation,
         right_arm_elevation)
```

This feature provides shoulder/upper-limb information that shoulder asymmetry alone cannot provide.

---

# 18. Why These Eight Features?

The feature set covers:

### Head/neck

```text
head_pitch
head_roll
forward_head_displacement
```

### Shoulders/upper limbs

```text
shoulder_asymmetry
upper_arm_elevation
```

### Torso

```text
torso_pitch
torso_lateral_tilt
torso_rotation
```

This gives coverage of the major upper-body regions relevant to the project's sitting-posture objective.

---

# 19. Features Removed During Selection

## `shoulder_symmetry`

Removed in favor of:

```text
shoulder_asymmetry
```

which directly expresses the left/right difference.

## `shoulder_forward_displacement`

Removed in favor of:

```text
upper_arm_elevation
```

which gives a more interpretable upper-limb posture variable.

## `hip_alignment_difference`

Excluded from the core classifier because the current scope emphasizes upper-body sitting posture and hip visibility can be less reliable in common webcam configurations.

## `hip_flexion_angle`

Excluded from the core eight because the current project is not attempting a complete lower-body ergonomic assessment.

## `spine_curvature_score`

Excluded because the available skeletal landmarks do not directly provide a complete anatomical spinal curve, making a composite curvature score difficult to interpret consistently.

---

# 20. Raw Coordinates vs Engineered Features

Instead of:

```text
33+ raw coordinates
       |
       v
Random Forest
```

the proposed pipeline is:

```text
Raw MediaPipe landmarks
       |
       v
Geometric transformations
       |
       v
8 interpretable features
       |
       v
Random Forest
```

This makes the model easier to:

- interpret
- debug
- reproduce
- explain in the paper
- deploy consistently

A raw-coordinate baseline can still be evaluated as a research comparison.

---

# 21. Normalization

Distance-based features should use body-scale normalization.

Examples:

```text
forward_head_displacement =
    displacement / torso_length

shoulder_asymmetry =
    shoulder_height_difference / shoulder_width
```

Angles remain in degrees.

Random Forest does not require standardization in the same way as many distance-based algorithms, so StandardScaler should not be applied automatically merely because it is common practice.

If other models are evaluated, preprocessing should be part of the model-specific pipeline.

---

# 22. Subject-wise Splitting

Do not perform a naive frame-level random split.

Bad:

```text
Frame 1 -> train
Frame 2 -> train
Frame 3 -> test
```

when all three come from the same participant.

Preferred:

```text
Participant IDs
       |
       +--------------------+
       |                    |
Training subjects     Held-out subjects
       |                    |
       v                    v
Model fitting        validation/test
```

A grouped cross-validation strategy is recommended.

A conceptual example is:

```text
13 subjects

9 -> training
2 -> validation
2 -> test
```

The actual split must preserve class coverage and be reported explicitly.

`subject` is used for grouping but is never passed to the classifier.

---

# 23. Final Engineered Dataset

The engineered dataset should contain:

```text
subject
head_pitch
head_roll
forward_head_displacement
torso_pitch
torso_lateral_tilt
torso_rotation
shoulder_asymmetry
upper_arm_elevation
upperbody_label
lowerbody_label
```

The main model uses:

```text
X =
[
    head_pitch,
    head_roll,
    forward_head_displacement,
    torso_pitch,
    torso_lateral_tilt,
    torso_rotation,
    shoulder_asymmetry,
    upper_arm_elevation
]

y =
upperbody_label
```

---

# 24. Model-ready Dataset

A clean model-ready table can be:

```text
head_pitch
head_roll
forward_head_displacement
torso_pitch
torso_lateral_tilt
torso_rotation
shoulder_asymmetry
upper_arm_elevation
posture_label
subject_group
```

where:

```text
posture_label =
    TUP
    TLB
    TLF
    TLR
    TLL
```

`subject_group` is metadata and must not be fed into the model.

---

# 25. Training and Live Inference Must Use the Same Feature Extractor

Training:

```text
MultiPosture
     |
     v
Feature Extractor
     |
     v
8 features
     |
     v
Random Forest
```

Production:

```text
Webcam
  |
  v
MediaPipe Pose
  |
  v
Feature Extractor
  |
  v
8 features
  |
  v
same Random Forest
```

These must match exactly:

- landmarks
- formulas
- coordinate system
- vector directions
- sign conventions
- normalization
- units
- feature order
- invalid-landmark behavior

Otherwise training-serving skew occurs.

---

# 26. Model

The initial classifier is:

```text
Random Forest
```

Input:

```text
8 engineered features
```

Output:

```text
TUP
TLB
TLF
TLR
TLL
```

Random Forest is suitable for the initial implementation because the feature space is small, nonlinear relationships can be captured, scaling is not mandatory, and feature importance can be inspected.

---

# 27. Evaluation

Report at least:

```text
Accuracy
Macro Precision
Macro Recall
Macro F1
Confusion Matrix
Per-class metrics
Subject-wise performance
```

Because participant leakage is a major concern, subject-wise evaluation should be emphasized.

---

# 28. Research Baselines

For a stronger research paper, compare:

### Baseline A

```text
Raw coordinates -> Random Forest
```

### Baseline B

```text
8 engineered features -> Random Forest
```

### Baseline C

```text
8 features -> Random Forest
              +
         temporal smoothing
```

### Proposed PostureAI pipeline

```text
8 engineered features
        +
Random Forest
        +
confidence
        +
personal baseline
        +
temporal risk modeling
```

This allows the contribution of each component to be evaluated rather than assumed.

---

# 29. RULA / ISO 11226 Relationship

RULA and ISO 11226 should be treated as **ergonomic context and validation frameworks**, not as the source dataset's labels.

Conceptually:

```text
MultiPosture
    |
    +--> supervised posture ground truth
    |
    v
PostureAI classifier

RULA / ISO 11226
    |
    +--> ergonomic interpretation
    |
    v
validation / discussion
```

Do not describe the eight features as a complete RULA or REBA implementation unless all required scoring components have actually been implemented.

Do not describe the source labels as medical diagnoses.

---

# 30. GOOD / MODERATE / BAD Risk Layer

The application-level risk state occurs after posture classification.

```text
                Random Forest
                     |
                     v
              posture prediction
                     |
                     v
                confidence
                     |
        +------------+------------+
        |                         |
        v                         v
 Personal baseline         temporal history
        |                         |
        +------------+------------+
                     |
                     v
              Risk Engine
                     |
                     v
              GOOD / MODERATE / BAD
```

Inputs may include:

1. posture prediction
2. prediction confidence
3. deviation from personal baseline
4. severity contribution
5. persistence
6. temporal smoothing

The resulting score is a **system-generated postural-risk indicator**, not a probability of injury or disease.

---

# 31. Personal Calibration

At the beginning of monitoring:

```text
Camera
  |
  v
Calibration period
  |
  v
Neutral sitting observations
  |
  v
Personal baseline
```

Potential baseline values:

```text
baseline_head_pitch
baseline_head_roll
baseline_forward_head
baseline_torso_pitch
baseline_torso_lateral_tilt
baseline_torso_rotation
baseline_shoulder_asymmetry
baseline_upper_arm_elevation
```

Then:

```text
deviation =
current_feature - baseline_feature
```

The baseline is an application reference for personalization, not a medical definition of ideal posture.

---

# 32. Temporal Modeling

A single frame should not automatically trigger a warning.

```text
Frame 1 -> prediction
Frame 2 -> prediction
Frame 3 -> prediction
...
Frame N -> prediction
              |
              v
       temporal modeling
              |
              v
       persistent state
```

One possible confidence-aware formulation is:

```text
R_t = α R_(t-1) + (1-α) p_t c_t
```

where:

- `R_t` = postural-risk indicator
- `α` = smoothing factor
- `p_t` = current abnormality/severity contribution
- `c_t` = model confidence

The exact risk formula and thresholds must be experimentally validated.

---

# 33. Important Monitoring States

The system must not convert tracking failures into bad posture.

Examples:

```text
TARGET_LOST
POSE_UNAVAILABLE
NOT_SITTING
LOW_CONFIDENCE
CAMERA_DISCONNECTED
```

These should be handled as system/observation states rather than:

```text
BAD
```

This prevents false alerts caused by missing or unreliable observations.

---

# 34. Alert Logic

Conceptually:

```text
Potentially bad posture
        |
        v
confidence check
        |
        v
temporal persistence
        |
        v
alert delay
        |
        v
user alert
```

An alert delay can be configurable. It should be validated experimentally rather than treated as a medical threshold.

---

# 35. Dataset Artifacts

Keep the pipeline reproducible with separate artifacts:

```text
data/
├── multiposture_raw.csv
├── multiposture_engineered.csv
└── posture_ml_dataset.csv
```

## Raw

Never overwrite the original dataset.

## Engineered

Contains:

```text
subject
8 engineered features
upperbody_label
lowerbody_label
```

## Model-ready

Contains:

```text
8 features
posture label
subject grouping metadata
```

---

# 36. Recommended Implementation Modules

```text
src/
├── data_loader.py
├── data_validator.py
├── landmark_selector.py
├── coordinate_utils.py
├── angle_utils.py
├── feature_extractor.py
├── dataset_builder.py
├── dataset_splitter.py
└── train_classifier.py
```

Responsibilities:

### `data_loader.py`

Loads the raw CSV.

### `data_validator.py`

Checks missing values, invalid values, labels, duplicates and landmark availability.

### `landmark_selector.py`

Maps raw CSV columns to semantic landmarks.

### `coordinate_utils.py`

Handles vectors, distances, normalization and coordinate transformations.

### `angle_utils.py`

Handles signed angles and relative orientations.

### `feature_extractor.py`

Produces exactly the eight features.

### `dataset_builder.py`

Generates the engineered dataset.

### `dataset_splitter.py`

Creates subject-wise train/validation/test groups.

### `train_classifier.py`

Trains and evaluates the Random Forest.

---

# 37. Feature Extractor Contract

The implementation should expose one stable function:

```python
features = extract_features(landmarks)
```

returning:

```python
{
    "head_pitch": ...,
    "head_roll": ...,
    "forward_head_displacement": ...,
    "torso_pitch": ...,
    "torso_lateral_tilt": ...,
    "torso_rotation": ...,
    "shoulder_asymmetry": ...,
    "upper_arm_elevation": ...
}
```

The same mathematical definitions must be used offline and during live inference.

---

# 38. Engineered Dataset Quality Checks

After generation, create:

## Missing-value report

```text
feature                         missing %
-----------------------------------------
head_pitch                     ...
head_roll                      ...
forward_head_displacement      ...
torso_pitch                    ...
torso_lateral_tilt             ...
torso_rotation                 ...
shoulder_asymmetry             ...
upper_arm_elevation            ...
```

## Distribution report

For every feature:

- minimum
- maximum
- mean
- median
- standard deviation
- percentiles

## Label distribution

```text
TUP
TLB
TLF
TLR
TLL
```

## Subject distribution

Verify every subject contributes sufficient samples.

## Correlation

Generate a feature-correlation matrix and investigate highly redundant pairs.

---

# 39. Final Data Flow for the Report

```text
                         RAW MULTIPOSTURE
                                |
                                v
                     +--------------------+
                     | Data Validation    |
                     +---------+----------+
                               |
                               v
                     +--------------------+
                     | Landmark Selection |
                     +---------+----------+
                               |
                               v
                     +--------------------+
                     | Feature Engineering|
                     +---------+----------+
                               |
             +-----------------+------------------+
             |                 |                  |
             v                 v                  v
         HEAD/NECK        SHOULDERS/ARMS       TORSO
             |                 |                  |
         3 features         2 features         3 features
             |                 |                  |
             +-----------------+------------------+
                               |
                               v
                         8 FEATURES
                               |
                               v
                   SUBJECT-WISE SPLIT
                               |
                               v
                       RANDOM FOREST
                               |
                               v
                 TUP/TLB/TLF/TLR/TLL
                               |
                               v
                 CONFIDENCE + BASELINE
                               |
                               v
                    TEMPORAL RISK ENGINE
                               |
                               v
                    GOOD/MODERATE/BAD
```

---

# 40. What the Project Can and Cannot Claim

## Can claim

- Webcam-based sitting-posture recognition.
- MediaPipe skeletal landmark extraction.
- Geometric posture feature engineering.
- Head/neck, shoulder/arm and trunk feature coverage.
- Supervised classification of the MultiPosture upper-body posture classes.
- Personalized baseline comparison.
- Confidence-aware temporal risk interpretation.
- Ergonomic alignment/context using established frameworks.

## Should not claim

- MultiPosture contains medical GOOD/MODERATE/BAD ground truth.
- The model diagnoses musculoskeletal disease.
- The risk score is an injury probability.
- MediaPipe gives clinically exact spinal measurements.
- The eight features alone constitute full RULA/REBA.
- A particular feature threshold is medically unsafe unless externally validated.

---

# 41. Final Frozen Specification

### Raw input

```text
MultiPosture CSV
```

### Metadata

```text
subject
```

### Source target

```text
upperbody_label
```

### Source posture classes

```text
TUP
TLB
TLF
TLR
TLL
```

### Engineered features

```text
1. head_pitch
2. head_roll
3. forward_head_displacement
4. torso_pitch
5. torso_lateral_tilt
6. torso_rotation
7. shoulder_asymmetry
8. upper_arm_elevation
```

### Classifier

```text
Random Forest
```

### Application-level risk layer

```text
posture prediction
+
confidence
+
personal baseline
+
temporal persistence
        |
        v
GOOD / MODERATE / BAD
```

---

# 42. Implementation Freeze Checklist

Before training:

- [ ] Preserve raw CSV unchanged.
- [ ] Verify every required landmark column.
- [ ] Define missing-value policy.
- [ ] Define duplicate policy.
- [ ] Freeze coordinate convention.
- [ ] Freeze vector directions.
- [ ] Freeze angle formulas.
- [ ] Freeze sign conventions.
- [ ] Freeze normalization formulas.
- [ ] Freeze the eight features.
- [ ] Freeze bilateral-arm aggregation.
- [ ] Implement subject-wise splitting.
- [ ] Generate engineered CSV.
- [ ] Inspect distributions.
- [ ] Inspect feature correlation.
- [ ] Inspect class balance.
- [ ] Verify no subject leakage.
- [ ] Reuse the same feature-extraction logic in live inference.
- [ ] Only then train the Random Forest.

---

# 43. Immediate Next Step

Do **not** train the model yet.

The conceptual dataset design is frozen, but the next technical task is to derive and implement the **exact mathematical formulas for the eight features from the actual CSV columns**.

The next pipeline should be:

```text
actual raw CSV
      |
      v
exact landmark mapping
      |
      v
exact mathematical feature formulas
      |
      v
multiposture_engineered.csv
      |
      v
distribution + correlation + class analysis
      |
      v
validate feature behavior
      |
      v
train Random Forest
```

This document should be treated as the project's dataset specification for the report, research paper and implementation.
