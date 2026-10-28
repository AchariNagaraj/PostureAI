# POSTUREAI — COMPLETE MASTER PROJECT CONTEXT
## Authoritative Architecture + Full Module Specification + All Phases
**Version:** 2026-09-27  
**Purpose:** Single source of truth for implementation, research, testing, diagrams, and future AI-agent work.

> **Important:** This document intentionally preserves the historical project context after this authoritative section. Where older sections conflict with the current architecture, the authoritative section wins.

---

# 0. CURRENT NON-NEGOTIABLE DECISIONS

## 0.1 Project identity

**Project:** PostureAI

**Purpose:** Real-time webcam-based sitting-posture monitoring for general users.

**Product boundary:** This is a posture-monitoring / decision-support system, not a medical diagnostic system.

---

## 0.2 Final ML architecture

The project uses **ONE unified posture model**, not separate front-view and side-view models.

```text
                    WEBCAM
                       |
                       v
               Person Detection
                       |
                       v
                Target Selection
                       |
                       v
                 Target Tracking
                       |
                       v
              Viewpoint Estimation
                       |
                       v
                 MediaPipe Pose
                       |
                       v
       Canonical / Viewpoint-Aware Pose
                       |
                       v
              ONE Feature Pipeline
                       |
                       v
               ONE Posture Model
                       |
                       v
          Prediction + Confidence
                       |
                       v
             Temporal Risk Engine
                       |
                       v
          Stable State + Alert Logic
                       |
                       v
        Voice + Visual Recommendation
```

The viewpoint is an input/context variable. It does **not** select a separate model.

---

# 0.3 Final supported viewpoints

```text
FRONT
LEFT_3_4
RIGHT_3_4
LEFT_PROFILE
RIGHT_PROFILE
UNKNOWN
```

The system should determine the approximate viewpoint from the observed body geometry and use that information to make the same feature representation consistent across orientations.

---

# 0.4 Side-view strategy — SAME DATASET

A side-view capable system is required without creating a separate side-view model.

The core principle is:

> **Use the same MultiPosture dataset, the same landmark representation, the same engineered feature definitions, and the same unified posture model.**

The available MultiPosture data is primarily 3D skeletal data. It does **not** provide complete real-world side-view webcam coverage. Therefore:

```text
MultiPosture 3D landmarks
        |
        +--> original viewpoint
        |
        +--> controlled geometric viewpoint transformations
        |
        v
same 8 engineered features
        |
        v
same posture labels
        |
        v
same unified model
```

### Side-view implementation

For viewpoint augmentation:

1. Start from the original raw 3D landmarks.
2. Never rotate already-engineered scalar features.
3. Apply controlled rotations to the raw landmark coordinates.
4. Recalculate the exact same feature extractor after transformation.
5. Preserve posture semantics.
6. Track the original sample ID, subject ID, source viewpoint, transformed viewpoint, and whether the sample is REAL or SYNTHETIC.
7. Never allow synthetic variants of a final test subject to enter training.
8. Inspect coordinate conventions before deciding the semantic meaning of positive/negative yaw.
9. Use viewpoint/canonical representation to make the feature vector consistent.
10. Train one unified classifier.

### Critical research limitation

Synthetic viewpoint transformation is **not equivalent to real side-view validation**.

The project may say:

> The model was trained/evaluated using viewpoint-augmented representations derived from the same MultiPosture 3D dataset.

It must not say:

> The model has been validated on real side-view webcam data

unless a separately labeled real side-view dataset is actually collected and evaluated.

---

# 0.5 FINAL 8 FEATURES

The current authoritative feature vector contains exactly:

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

### Feature semantics

| Feature | Meaning |
|---|---|
| `head_pitch` | Head/neck flexion-extension orientation |
| `head_roll` | Head/neck side-bending orientation |
| `forward_head_displacement` | Forward displacement of head relative to body reference |
| `torso_pitch` | Trunk forward/backward inclination |
| `torso_lateral_tilt` | Trunk side-bending |
| `torso_rotation` | Trunk axial rotation/twist |
| `shoulder_asymmetry` | Difference/asymmetry between shoulder geometry |
| `upper_arm_elevation` | Elevation of upper arm relative to torso |

`torso_pitch`, `torso_lateral_tilt`, `torso_rotation`, and `upper_arm_elevation` have meaningful ergonomic interpretation. `forward_head_displacement` and `shoulder_asymmetry` are engineered ML features and do not automatically have universal clinical thresholds.

---

# 0.6 FINAL POSTURE CLASSES

The ML classifier currently predicts five upper-body posture classes:

```text
TUP = Upright trunk
TLB = Trunk leaning backward
TLF = Trunk leaning forward
TLL = Trunk leaning left
TLR = Trunk leaning right
```

These are **not** the same thing as application-level risk bands.

The architecture is:

```text
5-class ML posture
        |
        v
confidence
        |
        v
temporal state
        |
        v
application-level postural risk
        |
        v
alert / recommendation
```

Do not silently replace the five classes with GOOD/MODERATE/BAD.

---

# 0.7 FINAL DATASET

Primary dataset:

**MultiPosture**

Known characteristics:

- 13 participants
- approximately 4,800 frames
- MediaPipe Pose Heavy
- 3D skeletal coordinates
- coordinates normalized relative to hip center
- subject metadata
- manually labeled upper/lower body posture
- upper-body labels:
  - TUP
  - TLB
  - TLF
  - TLL
  - TLR
- lower-body labels retained as metadata/secondary target
- `subject` is metadata, never an ML feature

Final engineered file:

```text
data/multiposture_engineered.csv
```

The dataset engineering stage is frozen unless a measured experiment requires a new version.

---

# 0.8 FINAL BASELINE ML RESULT

Baseline model:

```text
Random Forest
200 trees
n_jobs = -1
subject-wise split
```

Exact eight features listed above.

Held-out test subjects:

```text
[1, 9, 12]
```

Development subjects:

```text
[2, 3, 4, 5, 6, 7, 8, 10, 11, 13]
```

Previously recorded held-out results:

```text
Accuracy  = 0.975925925925926
Weighted Precision = 0.9774626251910524
Weighted Recall    = 0.975925925925926
Weighted F1        = 0.9751074988246377
```

Confusion matrix label order:

```text
["TLB", "TLF", "TLL", "TLR", "TUP"]
```

Matrix:

```text
[
 [154, 0,   0, 0, 0],
 [0,   284, 0, 0, 1],
 [0,   23,  96,0, 1],
 [0,   0,   0, 120,0],
 [1,   0,   0, 0, 400]
]
```

Main observed confusion:

```text
TLL -> TLF
23 samples
```

Do not generalize this result to real webcam side-view accuracy.

---

# 0.9 CURRENT MODEL ARTIFACTS

```text
data/multiposture_engineered.csv
models/viewpoint_robust_model.joblib
ml/models/posture_model.joblib

reports/ml/evaluation.json
reports/ml/evaluation.txt
reports/ml/confusion_matrix.png
reports/ml/split_subjects.json

data/multiposture_viewpoint_augmented.csv
reports/ml/viewpoint/final_test_evaluation.json
```

---

# 0.10 MODEL LOADING REQUIREMENT

The model must be:

- loaded once;
- reused for inference;
- never retrained during a live session;
- versioned;
- accompanied by its feature schema;
- checked for compatibility before inference.

Inference must verify:

```text
live feature names
        ==
training feature names

live feature order
        ==
training feature order

live transformations
        ==
training transformations
```

---

# 1. COMPLETE END-TO-END ARCHITECTURE

```text
                           USER
                             |
                             v
                    React + Vite + Tailwind
                             |
                       HTTPS / WSS
                             |
                             v
                Load Balancer / Reverse Proxy
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
          FastAPI 1      FastAPI 2      FastAPI 3
              |              |              |
              +--------------+--------------+
                             |
                             v
                           Redis
                             |
                   ML Worker Coordination
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
         ML Worker 1     ML Worker 2     ML Worker 3+
             |               |               |
             +---------------+---------------+
                             |
                             v
                     Monitoring Engine
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
       Live State       Aggregation        Alert/Voice
          |                  |                  |
          v                  v                  v
      WebSocket            Redis              User
                             |
                             v
                           MySQL
```

---

# 2. LIVE ML PIPELINE — EVERY STAGE

```text
Browser Webcam
      |
      v
Camera Lifecycle
      |
      v
Latest Frame Buffer
      |
      v
Person Detection
      |
      v
Target Selection
      |
      v
Target Tracking
      |
      v
Viewpoint Estimation
      |
      v
MediaPipe Pose
      |
      v
Pose Validation
      |
      v
Sitting-State Gate
      |
      v
Canonical / Viewpoint-Aware Representation
      |
      v
Feature Extraction
      |
      v
Personal Baseline Normalization
      |
      v
Unified Posture Model
      |
      v
Class Probabilities
      |
      v
Prediction Confidence
      |
      v
Temporal Risk Engine
      |
      v
Stable Posture/Risk State
      |
      +-------------------+
      |                   |
      v                   v
Recommendation       Alert Engine
                          |
                    +-----+------+
                    |            |
                    v            v
               Visual Alert   Voice Alert
```

---

# 3. MODULE-BY-MODULE SPECIFICATION

This section defines what each logical module is responsible for, what it receives, what it produces, and what it must **not** own.

---

## 3.1 `frame_manager`

### Responsibility

Own camera-frame freshness.

### Contains

- latest-frame storage;
- timestamp;
- frame replacement;
- stale-frame detection;
- optional frame-rate statistics.

### Input

```text
camera frame
timestamp
```

### Output

```text
latest valid frame
frame timestamp
```

### Rules

- Do not maintain an unbounded queue.
- Drop stale frames.
- ML should process the newest useful frame.
- Camera FPS and ML FPS are different.

### Failure states

```text
NO_FRAME
STALE_FRAME
CAMERA_DISCONNECTED
```

---

## 3.2 `person_detector`

### Responsibility

Determine whether people are visible.

### Output

```text
NO_PERSON
ONE_PERSON
MULTIPLE_PEOPLE
```

and detected person regions/identifiers sufficient for target selection.

### Important

It does not decide who the authenticated user is.

It does not use face recognition.

---

## 3.3 `target_selector`

### Responsibility

Allow the user to explicitly select the person to monitor.

### Flow

```text
MULTIPLE_PEOPLE
      |
      v
Display selectable targets
      |
      v
User chooses target
      |
      v
TARGET_CONFIRMED
```

### Rules

- Never guess when multiple people exist.
- Never silently switch targets.
- Re-selection is required after unrecoverable target loss.

---

## 3.4 `person_tracker`

### Responsibility

Maintain identity continuity for the selected target.

### States

```text
SEARCHING
TRACKING
TEMPORARILY_LOST
TARGET_LOST
AWAITING_CONFIRMATION
RESELECT_REQUIRED
```

### Contains

- selected target state;
- bounding box continuity;
- tracking confidence;
- target-loss timer;
- recovery logic.

### Critical behavior

```text
A selected
   |
B crosses
   |
tracker becomes uncertain
   |
attempt to recover A
   |
NEVER switch to B automatically
```

Candidate target-loss grace period:

```text
~2–3 seconds
```

This is an engineering parameter, not a validated human-factors threshold.

---

## 3.5 `viewpoint_estimator`

### Responsibility

Estimate approximate camera/body orientation.

### Output

```text
FRONT
LEFT_3_4
RIGHT_3_4
LEFT_PROFILE
RIGHT_PROFILE
UNKNOWN
```

### Why it exists

The same posture may produce different raw landmark geometry from different viewpoints.

The estimator provides orientation context so the representation can remain consistent.

### It does NOT

- choose a different model;
- create separate front/side classifiers;
- guarantee exact camera pose;
- infer physical camera yaw unless explicitly implemented and validated.

---

## 3.6 `pose_estimator`

### Responsibility

Run MediaPipe Pose on the selected target.

### Output

3D body landmarks plus visibility/confidence information.

### Important

Pose estimation failure is not BAD posture.

---

## 3.7 `pose_validator`

### Responsibility

Determine whether the landmarks required for the posture feature vector are usable.

### Checks

- required landmarks exist;
- visibility is sufficient;
- values are finite;
- body geometry is plausible;
- target continuity is acceptable.

### Output

```text
POSE_VALID
POSE_UNAVAILABLE
```

---

## 3.8 `sitting_gate`

### Responsibility

Ensure the product only classifies sitting posture when the person is actually sitting.

### State model

```text
SITTING
NOT_SITTING
UNKNOWN
```

### Behavior

```text
SITTING      -> posture classifier enabled
NOT_SITTING  -> posture classification paused
UNKNOWN      -> insufficient information
```

### Critical rule

Standing is not BAD sitting posture.

---

## 3.9 `canonical_representation`

### Responsibility

Convert viewpoint-dependent landmarks into a body-centered/viewpoint-aware representation.

### Concept

```text
Raw 3D landmarks
       |
       v
Hip center
Shoulder center
Shoulder axis
Torso axis
       |
       v
Body-centered coordinates
       |
       v
Consistent orientation
```

### Important

This module operates on **raw landmarks**, not on already-computed scalar features.

---

## 3.10 `feature_extractor`

### Responsibility

Compute the exact eight final features.

### Output schema

```text
head_pitch
head_roll
forward_head_displacement
torso_pitch
torso_lateral_tilt
torso_rotation
shoulder_asymmetry
upper_arm_elevation
```

### Requirements

- same mathematical definitions during training and inference;
- same units;
- same coordinate conventions;
- same handling of missing landmarks;
- deterministic output order.

---

## 3.11 `calibration`

### Responsibility

Collect the user's comfortable upright reference.

### Proposed initial durations

```text
First use:       ~10–15 seconds
Returning user:  ~3–5 seconds
```

These are engineering starting points only.

### Process

```text
Start calibration
      |
collect valid frames
      |
discard invalid observations
      |
robust aggregation
      |
baseline profile
      |
calibration complete
```

Use a median/robust estimator rather than one frame.

---

## 3.12 `baseline_normalizer`

### Responsibility

Convert absolute feature values into deviations relative to the user's baseline.

Conceptually:

```text
current_feature - baseline_feature
                |
                v
normalized deviation
```

### Purpose

Reduce sensitivity to:

- body proportions;
- natural posture differences;
- camera distance;
- setup variation.

### Research experiment

```text
No baseline
vs
Personal baseline
```

---

## 3.13 `posture_classifier`

### Responsibility

Run the single unified ML model.

### Current model

```text
Random Forest
```

### Input

Exactly the final eight features after the agreed representation/normalization.

### Output

Five-class prediction:

```text
TUP
TLB
TLF
TLL
TLR
```

plus class probabilities.

### Important

The classifier does not generate alerts.

---

## 3.14 `confidence_engine`

### Responsibility

Quantify how strongly the current model observation should influence temporal state.

For five-class output:

```text
C_t = max(
  P(TUP),
  P(TLB),
  P(TLF),
  P(TLL),
  P(TLR)
)
```

### Important

Random Forest probabilities are not automatically perfectly calibrated probabilities.

If confidence thresholds drive behavior, evaluate probability calibration on held-out data.

---

## 3.15 `temporal_risk_engine`

### Responsibility

Convert noisy frame-level five-class predictions into a stable application-level postural-risk state.

### IMPORTANT CURRENT DESIGN

Because the ML model predicts five posture classes, the old direct:

```text
P(GOOD)
P(MODERATE)
P(BAD)
```

formula cannot be copied unchanged.

A mapping from five posture classes to application-level severity must be explicitly defined and experimentally validated.

One candidate mapping is:

```text
TUP -> 0.0
TLB -> 0.5 or configurable
TLF -> 1.0
TLL -> 1.0
TLR -> 1.0
```

but this is an **engineering candidate**, not a validated ergonomic scale.

An alternative is to map each class to severity using feature/ergonomic evidence. This decision must be frozen before implementation of the final risk score.

### Required inputs

```text
class probabilities
predicted posture
confidence
previous risk
elapsed time
tracking state
pose validity
sitting state
```

### Required outputs

```text
risk_score
risk_level
stable_posture
persistence_state
```

### Time-based behavior

Do not use frame count as duration.

Use timestamps:

```text
delta_t = current_timestamp - previous_timestamp
```

A temporal decay form can be:

```text
alpha_t = exp(-delta_t / tau)
```

Then:

```text
R_t = alpha_t * R_(t-1)
      + (1-alpha_t) * E_t
```

where `E_t` is the confidence-aware current observation.

The final severity mapping and parameters remain experimental until validated.

---

## 3.16 `risk_engine`

### Responsibility

Maintain application-level stable postural risk.

### It is distinct from

- raw ML class;
- classifier confidence;
- alert generation.

### Example state

```json
{
  "stable_posture": "TLF",
  "risk_score": 0.78,
  "risk_level": "HIGH",
  "confidence": 0.91
}
```

Illustrative only.

---

## 3.17 `alert_engine`

### Responsibility

Determine whether the user should actually be alerted.

### Principle

```text
BAD/deviant frame
      !=
ALERT
```

Instead:

```text
persistent deviation
      +
sufficient confidence
      +
valid sitting state
      +
not in cooldown
      |
      v
ALERT
```

### State machine

```text
NORMAL
  |
  v
PERSISTENT_ABNORMAL
  |
  v
ALERTED
  |
  v
COOLDOWN
  |
  v
NORMAL
```

### Candidate parameters

```text
bad posture persistence ~= 10 seconds
activation threshold ~= 0.70
recovery threshold   ~= 0.50
cooldown = configurable
```

These are engineering parameters, not clinical thresholds.

---

# 4. VOICE ALERT MODULE — NEW PRODUCT REQUIREMENT

Voice alerts are now an explicit part of PostureAI.

## 4.1 Purpose

When an alert is justified, the system may provide:

1. visual alert;
2. application sound;
3. **spoken voice message**.

---

## 4.2 Voice flow

```text
Temporal Risk Engine
        |
        v
Alert Engine
        |
        +--> Visual Alert
        |
        +--> Browser Notification
        |
        +--> Voice Alert
                  |
                  v
          Recommendation Text
                  |
                  v
       Browser Speech Synthesis
                  |
                  v
                User
```

---

## 4.3 Voice message examples

For forward trunk lean:

> "You have been leaning forward for a while. Please sit more upright."

For backward lean:

> "Your trunk has been leaning backward. Try to return to a neutral sitting position."

For lateral lean:

> "Your posture is leaning to one side. Try to center your upper body."

For forward head:

> "Your head is positioned too far forward. Try bringing your head back toward a neutral position."

These are product examples and should be refined after testing.

---

## 4.4 Voice rules

Voice must obey the same alert state machine.

Never:

```text
speak every frame
```

Instead:

```text
persistent abnormal state
        |
        v
alert eligibility
        |
        v
voice message
        |
        v
cooldown
```

---

## 4.5 Browser implementation

The initial browser implementation can use:

```text
Web Speech API / SpeechSynthesis
```

The frontend receives an alert/recommendation event through WebSocket and speaks it.

### Browser restriction

Audio/speech can be restricted until the user interacts with the page.

Therefore:

```text
Start Monitoring
      |
      v
initialize audio/speech permission path
```

Do not assume voice playback is guaranteed when the browser is closed, background-restricted, asleep, or unavailable.

---

# 5. RECOMMENDATION ENGINE

Recommendations are generated from the stable posture state and/or dominant feature deviation.

```text
Stable posture/risk
       |
       v
Posture semantics
       |
       v
Recommendation
       |
       +--> UI card
       +--> alert text
       +--> voice message
```

The recommendation engine should not directly decide risk.

---

# 6. MONITORING SESSION MODULE

A monitoring session is different from login authentication.

## Login session

```text
Who is authenticated?
```

## Monitoring session

```text
When did actual posture monitoring start?
When did it end?
What happened during it?
```

### Session lifecycle

```text
REQUESTED
   |
   v
INITIALIZING
   |
   v
CALIBRATING
   |
   v
ACTIVE
   |
   +--> PAUSED
   |
   +--> TEMPORARILY_DISCONNECTED
   |
   +--> TARGET_LOST
   |
   +--> AWAITING_CONFIRMATION
   |
   v
COMPLETED
```

---

# 7. SESSION AGGREGATOR

The system must not write every frame to MySQL.

Instead:

```text
Frame-level inference
       |
       v
In-memory/session accumulator
       |
       v
Periodic aggregation
       |
       v
Redis
       |
       v
MySQL
```

Potential aggregation:

```text
posture durations
average risk
maximum risk
average confidence
feature summaries
alert count
tracking-loss count
```

---

# 8. DATABASE MODULES

## `users`

```text
id PK
name
email UNIQUE
password_hash
created_at
```

## `user_settings`

```text
id PK
user_id FK
notification_enabled
sound_enabled
voice_enabled
alert_delay
voice_volume
```

`voice_enabled` is added explicitly for the new voice-alert requirement.

## `sessions`

Current product schema must be reconciled with the five-class ML model.

Prefer storing:

```text
session_id
user_id
started_at
ended_at
duration
average_risk
max_risk
total_alerts
```

and class/posture distributions rather than pretending the ML model directly predicts GOOD/MODERATE/BAD.

## `posture_metrics`

```text
id PK
session_id FK
timestamp
posture_distribution
average_risk
average_confidence
feature summaries
```

## `alerts`

```text
id PK
session_id FK
timestamp
alert_type
posture
risk_score
message
voice_delivered
```

`voice_delivered` allows the system to distinguish a generated voice alert from an alert that could not be played.

---

# 9. REDIS MODULE

Redis is for transient/live data.

### Contains

- live session state;
- queues;
- worker coordination;
- temporary persistence buffering;
- reconnect state where appropriate.

### Does not contain

Permanent historical truth.

### Failure

Redis outage means degraded coordination/buffering.

Do not claim zero data loss.

---

# 10. FASTAPI MODULES

Suggested structure:

```text
backend/
└── app/
    ├── main.py
    ├── api/
    │   ├── auth.py
    │   ├── users.py
    │   ├── settings.py
    │   ├── sessions.py
    │   ├── reports.py
    │   ├── analytics.py
    │   └── websocket.py
    │
    ├── services/
    │   ├── auth_service.py
    │   ├── session_service.py
    │   ├── report_service.py
    │   ├── analytics_service.py
    │   ├── monitoring_service.py
    │   └── notification_service.py
    │
    ├── repositories/
    │   ├── user_repository.py
    │   ├── session_repository.py
    │   ├── metrics_repository.py
    │   └── alert_repository.py
    │
    ├── models/
    │   ├── user.py
    │   ├── user_setting.py
    │   ├── session.py
    │   ├── posture_metric.py
    │   └── alert.py
    │
    ├── schemas/
    │   ├── auth.py
    │   ├── session.py
    │   ├── posture.py
    │   ├── alert.py
    │   └── report.py
    │
    └── core/
        ├── security.py
        ├── config.py
        ├── database.py
        └── redis.py
```

### API responsibilities

Authentication:

```text
POST /auth/register
POST /auth/login
```

Profile/settings:

```text
GET /profile
GET /settings
PUT /settings
```

Monitoring:

```text
POST /sessions
POST /sessions/{id}/stop
GET /sessions
GET /sessions/{id}
```

Reports:

```text
GET /reports/{session_id}
```

Analytics:

```text
GET /analytics
```

WebSocket:

```text
WS /ws/monitoring/{session_id}
```

Exact endpoint names are implementation contracts and must be frozen before integration.

---

# 11. WEBSOCKET CONTRACT

Example live event:

```json
{
  "type": "POSTURE_UPDATE",
  "timestamp": 1750000000,
  "posture": "TLF",
  "confidence": 0.91,
  "risk_score": 0.78,
  "risk_level": "HIGH",
  "tracking_status": "TRACKING",
  "viewpoint": "RIGHT_3_4",
  "sitting_state": "SITTING",
  "recommendation": "Try to sit more upright.",
  "alert": true,
  "voice_alert": true
}
```

System events:

```text
MONITORING_STARTED
CALIBRATION_STARTED
CALIBRATION_COMPLETED
POSTURE_UPDATE
TARGET_LOST
POSE_UNAVAILABLE
NOT_SITTING
ALERT
VOICE_ALERT
RECONNECT_REQUIRED
SESSION_COMPLETED
ERROR
```

---

# 12. FRONTEND MODULES

```text
frontend/src/
├── pages/
│   ├── Login
│   ├── Register
│   ├── Dashboard
│   ├── LiveMonitor
│   ├── Reports
│   ├── Analytics
│   └── Settings
│
├── components/
│   ├── CameraView
│   ├── PoseOverlay
│   ├── TargetSelector
│   ├── ViewpointIndicator
│   ├── CalibrationPanel
│   ├── PostureStatus
│   ├── RiskIndicator
│   ├── AlertBanner
│   ├── VoiceAlertIndicator
│   ├── RecommendationCard
│   ├── SessionTimer
│   └── Charts
│
├── services/
│   ├── api
│   ├── websocket
│   ├── auth
│   └── speech
│
├── hooks/
│   ├── useCamera
│   ├── useMonitoring
│   ├── useWebSocket
│   └── useVoiceAlert
│
└── state/
    ├── auth
    ├── monitoring
    └── settings
```

---

# 13. `CameraView`

### Owns

- browser `getUserMedia`;
- camera permission;
- stream lifecycle;
- camera state.

### States

```text
INITIALIZING
READY
ACTIVE
DISCONNECTED
ERROR
STOPPED
```

It does not own ML inference.

---

# 14. `TargetSelector`

Displays detected people and lets the user select one.

It must clearly communicate:

```text
Select yourself
```

rather than trying to infer identity through face recognition.

---

# 15. `PoseOverlay`

Displays:

- skeleton;
- target bounding region;
- optional landmark visibility;
- optional viewpoint.

It is primarily a visualization layer.

It must not become the source of truth for ML state.

---

# 16. `PostureStatus`

Displays the current stable posture:

```text
UPRIGHT
LEANING FORWARD
LEANING BACKWARD
LEANING LEFT
LEANING RIGHT
```

The UI may use friendly wording while preserving the internal class code.

---

# 17. `RiskIndicator`

Displays application-level postural risk.

Important:

```text
Risk score != medical probability
```

---

# 18. `AlertBanner`

Shows:

- why an alert occurred;
- recommendation;
- alert timestamp;
- cooldown state where useful.

---

# 19. `VoiceAlertIndicator`

Shows that spoken feedback is enabled and/or recently delivered.

Settings:

```text
Voice Alerts ON/OFF
Sound ON/OFF
```

---

# 20. `useVoiceAlert`

Responsibilities:

- receive voice-enabled alert events;
- check user preference;
- prevent duplicate speech;
- enforce cooldown;
- invoke browser speech synthesis;
- handle browser speech errors.

Pseudo-flow:

```text
WebSocket alert
      |
      v
voice_enabled?
      |
      +-- NO --> visual only
      |
      +-- YES
             |
             v
       cooldown active?
             |
             +-- YES --> suppress
             |
             +-- NO
                    |
                    v
             speak recommendation
```

---

# 21. AUTHENTICATION MODULE

JWT direction.

Rules:

- secure password hashing;
- HTTPS in production;
- WSS in production;
- authorization checks;
- ownership checks;
- never trust arbitrary `user_id`;
- never expose database credentials;
- no raw webcam storage by default.

---

# 22. PRIVACY MODULE

Default:

```text
Webcam
  |
  v
Real-time processing
  |
  v
Features/results
  |
  v
Aggregates/events
  |
  v
MySQL
```

Not:

```text
Webcam
  |
  v
Permanent raw video
```

No face recognition.

No biometric embeddings.

---

# 23. ERROR AND FAILURE MODULE

The system must distinguish:

```text
NO_PERSON
MULTIPLE_PEOPLE
TARGET_LOST
POSE_UNAVAILABLE
NOT_SITTING
UNKNOWN
LOW_CONFIDENCE
NETWORK_DISCONNECTED
SERVER_ERROR
```

None should automatically become BAD posture.

---

# 24. COMPLETE STATE SEPARATION

This separation is mandatory:

```text
CAMERA STATE
    |
    v
PERSON STATE
    |
    v
TRACKING STATE
    |
    v
VIEWPOINT STATE
    |
    v
POSE STATE
    |
    v
SITTING STATE
    |
    v
POSTURE CLASS
    |
    v
CONFIDENCE
    |
    v
TEMPORAL RISK
    |
    v
ALERT STATE
    |
    v
VOICE/RECOMMENDATION
```

This prevents one subsystem from incorrectly treating another subsystem's failure as a posture problem.

---

# 25. RESEARCH EXPERIMENTS

## Experiment A — Personal baseline

```text
No baseline
vs
Personal baseline
```

Measure:

- classification;
- cross-subject stability;
- setup robustness;
- feature variance.

## Experiment B — Viewpoint robustness

```text
Original MultiPosture
+
controlled 3D viewpoint transformations
        |
        v
same 8 features
        |
        v
same model
```

Measure by viewpoint where valid.

Do not represent synthetic side-view performance as real side-view validation.

## Experiment C — Temporal model

```text
Raw prediction
vs
ordinary smoothing
vs
confidence-aware temporal risk
```

Measure:

- false alerts;
- missed persistent abnormal events;
- alert latency;
- state transitions;
- stability;
- recovery;
- occlusion behavior.

## Experiment D — Calibration duration

```text
5 sec
10 sec
15 sec
```

Measure baseline stability and downstream performance.

## Experiment E — Confidence calibration

Evaluate whether model probabilities are calibrated sufficiently for temporal weighting.

## Experiment F — FPS sensitivity

Test different processing rates and irregular timestamps.

## Experiment G — Target loss/recovery

Test:

- brief occlusion;
- long occlusion;
- person crossing;
- target reappearance.

## Experiment H — Real webcam validation

Collect a labeled validation set if claiming quantitative webcam performance.

---

# 26. TESTING PYRAMID

```text
                E2E
               /   \
          Integration
             /     \
          Module Tests
           /       \
       Unit Tests  Data Tests
```

### Unit tests

- feature formulas;
- viewpoint transformations;
- confidence;
- risk;
- alert state machine;
- recommendation mapping.

### Integration tests

```text
frame
 -> detection
 -> tracking
 -> pose
 -> features
 -> model
 -> confidence
 -> risk
 -> alert
```

### E2E

```text
browser
 -> FastAPI
 -> Redis
 -> ML worker
 -> monitoring
 -> WebSocket
 -> React
 -> alert/voice
```

---

# 27. FAILURE TEST MATRIX

| Failure | Required behavior |
|---|---|
| Camera permission denied | No active monitoring |
| Camera unavailable | Clear error |
| Camera disconnect | Pause/reconnect |
| No person | No posture classification |
| Multiple people | Explicit selection |
| Target temporary loss | Grace period |
| Target permanent loss | Re-selection |
| Person crosses | Never auto-switch |
| Pose missing | POSE_UNAVAILABLE |
| User stands | NOT_SITTING |
| Low confidence | Avoid aggressive state change |
| Short deviation | No immediate alert |
| Persistent deviation | Alert |
| Recovery | Reset persistence |
| Network loss | Reconnect or finalize |
| FastAPI restart | Recovery/reconnect |
| ML worker crash | Recover/reassign only if implemented |
| MySQL outage | Buffer compact data where possible |
| Redis outage | Degraded mode |
| Voice unavailable | Visual alert still works |

---

# 28. PERFORMANCE TARGETS VS MEASURED RESULTS

Do not confuse architecture targets with measured performance.

Possible targets:

```text
processing FPS: approximately 5–10
target users: approximately 100
target-loss grace: approximately 2–3 s
alert persistence: approximately 10 s
```

All must be measured and documented before being described as validated.

Metrics:

```text
FPS
inference latency
end-to-end latency
p50/p95/p99 latency
CPU
RAM
worker utilization
Redis latency
MySQL latency
queue delay
WebSocket latency
alert latency
tracking recovery time
```

---

# 29. SCALING ARCHITECTURE

Conceptual:

```text
                    Load Balancer
                         |
              +----------+----------+
              |          |          |
           FastAPI1   FastAPI2   FastAPI3
              |          |          |
              +----------+----------+
                         |
                       Redis
                         |
             +-----------+-----------+
             |           |           |
          Worker1     Worker2     Worker3+
                         |
                       MySQL
```

100 concurrent users is an architectural target, not a proven capacity result.

Load-test:

```text
10
25
50
75
100
```

and measure system behavior.

---

# 30. DOCKER DEPLOYMENT

Logical containers:

```text
frontend
fastapi
ml-worker
redis
mysql
reverse-proxy
```

Development can use Docker Compose.

Production topology remains dependent on load testing and deployment environment.

Docker does not itself provide fault tolerance.

---

# 31. COMPLETE DEVELOPMENT PHASES

## PHASE 0 — ENVIRONMENT STANDARDIZATION — COMPLETE

Tasks:

- standardize Python;
- pin dependencies;
- isolate `.venv`;
- verify MediaPipe;
- verify OpenCV;
- verify Pandas;
- verify scikit-learn;
- verify model loading;
- document setup.

---

## PHASE 1 — DATASET ENGINEERING + BASELINE ML — COMPLETE

Tasks:

1. inspect MultiPosture;
2. identify subjects;
3. verify labels;
4. engineer final features;
5. remove leakage;
6. split by subject;
7. train baseline;
8. evaluate;
9. save model;
10. verify reload.

Artifacts:

```text
data/multiposture_engineered.csv
ml/models/posture_model.joblib
reports/ml/*
```

---

## PHASE 1.5 — MODEL COMPARISON + SUBJECT-WISE CV — COMPLETE

Candidates:

```text
Logistic Regression
SVM RBF
Random Forest
Extra Trees
HistGradientBoosting
```

Method:

```text
development subjects
      |
      v
5-fold GroupKFold
groups = subject
      |
      v
model comparison
      |
      v
select model
      |
      v
train on all development subjects
      |
      v
evaluate once on untouched test subjects
```

Never tune using the final test subjects.

---

## PHASE 2 — UNIFIED VIEWPOINT SUPPORT — COMPLETE

Goal:

```text
front
3/4
profile
   |
   v
same representation
   |
   v
same feature extractor
   |
   v
same model
```

Tasks:

- start from raw 3D landmarks;
- apply controlled rotations;
- recalculate features;
- inspect directional semantics;
- create viewpoint metadata;
- preserve subject isolation;
- train unified model;
- verify reload.

Artifacts:

```text
data/multiposture_viewpoint_augmented.csv
models/viewpoint_robust_model.joblib
scripts/viewpoint_augmentation.py
scripts/train_viewpoint_model.py
scripts/verify_viewpoint_model.py
reports/ml/viewpoint/final_test_evaluation.json
```

---

## PHASE 3 — REAL-TIME WEBCAM ML — COMPLETE

Pipeline:

```text
Webcam
 -> latest frame
 -> detection
 -> target selection
 -> tracking
 -> viewpoint
 -> MediaPipe
 -> canonical representation
 -> 8 features
 -> unified model
 -> confidence
```

Requirements:

- model loaded once;
- stale frames dropped;
- stable target;
- no silent person switching;
- explicit pose failure;
- explicit viewpoint uncertainty;
- missing person/pose never treated as BAD.

---

## PHASE 4 — TEMPORAL RISK ENGINE — NEXT

This is the next major implementation phase.

Must implement:

- observation schema;
- five-class-to-severity mapping;
- confidence handling;
- temporal smoothing;
- persistence;
- recovery;
- duration;
- alert eligibility;
- cooldown;
- timestamp-based timing;
- invalid observation handling;
- session statistics;
- deterministic tests;
- experiments.

Pure module:

```text
ml/risk/temporal_risk_engine.py
```

Tests:

```text
tests/test_temporal_risk_engine.py
```

Experiment:

```text
scripts/experiments/temporal_risk_experiment.py
```

Report:

```text
reports/experiments/temporal_risk_engine_report.md
```

---

## PHASE 5 — FASTAPI + WEBSOCKET

Implement:

- authentication;
- authorization;
- monitoring session API;
- WebSocket;
- session ownership;
- live events;
- reconnect behavior;
- backend error handling.

---

## PHASE 6 — REACT + VITE + TAILWIND

Implement:

- Login;
- Register;
- Dashboard;
- LiveMonitor;
- Reports;
- Analytics;
- Settings;
- CameraView;
- TargetSelector;
- calibration;
- posture display;
- risk display;
- recommendation;
- visual alerts;
- voice alerts;
- WebSocket handling.

---

## PHASE 7 — REDIS + MYSQL

Implement:

- transient live state;
- worker coordination;
- persistence buffering;
- users;
- settings;
- sessions;
- posture metrics;
- alerts;
- idempotency.

Do not write every frame to MySQL.

---

## PHASE 8 — ALERTS + VOICE FEEDBACK

Implement:

- persistent abnormal-posture alert;
- visual alert;
- sound;
- browser notification;
- voice message;
- voice preference;
- speech cooldown;
- recommendation-to-speech mapping;
- graceful fallback if speech fails.

---

## PHASE 9 — ANALYTICS + REPORTS + RESEARCH EXPERIMENTS

Implement:

- session reports;
- historical charts;
- posture distribution;
- risk trends;
- alert history;
- feature summaries.

Run research experiments:

- personalization;
- viewpoint robustness;
- temporal ablation;
- confidence calibration;
- calibration duration;
- FPS sensitivity;
- occlusion;
- tracking;
- real webcam validation.

---

## PHASE 10 — FULL SYSTEM INTEGRATION

Integrate:

```text
React
  |
FastAPI
  |
Redis
  |
ML workers
  |
Monitoring Engine
  |
MySQL
```

Verify:

```text
camera
 -> target
 -> pose
 -> features
 -> model
 -> temporal risk
 -> alert
 -> voice
 -> persistence
 -> report
```

---

## PHASE 11 — PERFORMANCE + FAILURE + LOAD TESTING

Test:

```text
10
25
50
75
100
```

Measure:

- latency;
- throughput;
- CPU;
- RAM;
- queue delay;
- Redis;
- MySQL;
- WebSocket;
- worker utilization.

Failure tests:

- camera denial;
- disconnect;
- target loss;
- pose loss;
- network loss;
- FastAPI restart;
- ML worker restart;
- Redis outage;
- MySQL outage;
- browser refresh;
- duplicate session.

---

## PHASE 12 — DOCKER + DEPLOYMENT + HARDENING

Implement:

- Dockerfiles;
- Compose;
- environment variables;
- secret handling;
- reverse proxy;
- HTTPS/WSS;
- production logging;
- health checks;
- startup/shutdown;
- container resource limits;
- backup strategy.

---

## PHASE 13 — RESEARCH VALIDATION + FINAL DOCUMENTATION

Produce:

```text
problem statement
literature review
methodology
architecture
feature definitions
dataset methodology
ML methodology
viewpoint methodology
temporal methodology
experiments
results
failure analysis
limitations
privacy
security
deployment
conclusion
future work
```

Do not make novelty/medical claims without evidence.

---

# 32. RESEARCH PAPER ARCHITECTURE

Potential framing:

> A confidence-aware temporal framework for converting frame-level webcam posture predictions into stable continuous postural-risk states, using a unified viewpoint-aware representation and user-specific baseline normalization.

Potential research questions:

1. Does personal baseline normalization improve robustness across users and camera setups?
2. Does confidence-aware temporal modeling reduce false alerts compared with raw prediction and ordinary smoothing?
3. How robust is the unified model under controlled viewpoint transformations?
4. How does continuous monitoring compare with established ergonomic assessment concepts such as RULA/REBA?

RULA/REBA are ergonomic assessment methodologies, not medical diagnoses or automatic ground truth.

---

# 33. RESEARCH BASELINES

```text
Rule/threshold baseline
        vs
Random Forest only
        vs
Random Forest + ordinary smoothing
        vs
Random Forest + baseline normalization
        vs
Random Forest + confidence + temporal model
```

Optional:

```text
automated RULA
automated REBA
```

only when the mapping is rigorously defined.

---

# 34. IMPORTANT LIMITATIONS

The final documentation must state:

- MultiPosture does not provide complete real side-view webcam coverage.
- Viewpoint augmentation is synthetic/control-based transformation, not real side-view validation.
- Real webcam accuracy requires labeled webcam evaluation.
- Sitting-state validation must be explicit.
- Temporal thresholds are engineering parameters until validated.
- Risk bands are application-level states, not medical thresholds.
- Random Forest probabilities are not automatically calibrated.
- High held-out dataset accuracy does not establish clinical effectiveness.
- 100-user capacity must be measured.
- RULA/REBA are not medical ground truth.
- Novelty requires literature review.

---

# 35. SECURITY

Requirements:

```text
secure password hashing
JWT/equivalent authentication
authorization
ownership checks
HTTPS
WSS
secret management
no raw video by default
no face recognition
minimal stored data
protected Redis/MySQL
input validation
rate limiting where needed
logging without sensitive video
```

---

# 36. LOOP ENGINEERING RULE

Every implementation phase follows:

```text
INSPECT
   ↓
PLAN SMALL STEP
   ↓
IMPLEMENT
   ↓
RUN
   ↓
VERIFY
   ↓
FIX
   ↓
REGRESSION TEST
   ↓
DOCUMENT
   ↓
UPDATE STATUS
```

Never mark a phase complete because code exists.

A phase is complete only after:

```text
implementation
+
execution
+
verification
+
tests
+
regression
+
documentation
```

---

# 37. TARGET PROJECT STRUCTURE

```text
POSTUREAI/
├── .context/
│   ├── PROJECT_CONTEXT.md
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── DEVELOPMENT_RULES.md
│   ├── CURRENT_STATUS.md
│   ├── DECISIONS.md
│   ├── dataset/
│   ├── research/
│   ├── diagrams/
│   └── features/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── archive/
│
├── reports/
│   ├── dataset/
│   ├── experiments/
│   ├── performance/
│   └── ml/
│
├── scripts/
│   ├── dataset/
│   └── experiments/
│
├── ml/
│   ├── feature_engineering/
│   ├── viewpoint/
│   ├── models/
│   ├── tracking/
│   ├── risk/
│   └── inference/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── core/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── state/
│   └── tests/
│
├── models/
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── docker-compose.yml
```

---

# 38. FIVE PRIMARY DIAGRAMS

## Diagram 1 — System Architecture

```text
+------------------+
|      USER        |
+--------+---------+
         |
         v
+---------------------------+
| React + Vite + Tailwind   |
+------------+--------------+
             |
          HTTPS/WSS
             |
             v
+---------------------------+
| Load Balancer / Proxy     |
+------------+--------------+
             |
       +-----+-----+
       |     |     |
       v     v     v
    FastAPI FastAPI FastAPI
       \      |      /
        \     |     /
             v
          +------+
          |Redis |
          +--+---+
             |
      +------+------+
      |      |      |
      v      v      v
   Worker Worker Worker
      \      |      /
       \     |     /
        +----+----+
             |
             v
     Monitoring Engine
             |
       +-----+------+
       |            |
       v            v
    WebSocket     Aggregator
       |            |
       v            v
     React        Redis
                    |
                    v
                  MySQL
```

---

## Diagram 2 — Detailed ML Pipeline

```text
WEBCAM
  |
  v
Latest Frame Buffer
  |
  v
Person Detection
  |
  v
Target Selection
  |
  v
Target Tracking
  |
  v
Viewpoint Estimation
  |
  v
MediaPipe Pose
  |
  v
Pose Validation
  |
  v
Sitting-State Gate
  |
  v
Canonical/Viewpoint-Aware Representation
  |
  v
8 Feature Extraction
  |
  v
Personal Baseline Normalization
  |
  v
ONE Unified Posture Model
  |
  +--> TUP
  +--> TLB
  +--> TLF
  +--> TLL
  +--> TLR
  |
  v
Class Probabilities
  |
  v
Confidence
  |
  v
Temporal Risk
  |
  v
Stable Risk/Posture
  |
  +--> Recommendation
  |
  +--> Visual Alert
  |
  +--> Voice Alert
```

---

## Diagram 3 — Viewpoint / Same-Dataset Strategy

```text
                    MultiPosture
                  3D Raw Landmarks
                         |
             +-----------+-----------+
             |                       |
       Original Samples      Controlled 3D Rotation
                                     |
                                     v
                         FRONT / 3/4 / PROFILE
                                     |
             +-----------------------+
             |
             v
      Same Canonical Representation
             |
             v
       Same 8 Features
             |
             v
       Same Posture Labels
             |
             v
       ONE Unified Model
             |
             v
       Viewpoint-Robust Output
```

### Research boundary

```text
Synthetic viewpoint augmentation
            !=
real side-view validation
```

---

## Diagram 4 — Temporal + Alert + Voice

```text
Frame Prediction
      |
      v
Class Probabilities
      |
      v
Confidence
      |
      v
Temporal Smoothing
      |
      v
Persistence
      |
      v
Stable Risk
      |
      v
Alert Eligibility
      |
      +------------+
      |            |
      v            v
Visual Alert    Voice Alert
      |            |
      +------v-----+
             |
             v
       Recommendation
             |
             v
           User
```

---

## Diagram 5 — Database ER

```text
+----------------+
|     USERS      |
+-------+--------+
        |
        +------------------+
        |                  |
        v                  v
+---------------+   +---------------+
| USER_SETTINGS |   |   SESSIONS    |
+---------------+   +-------+-------+
                            |
                   +--------+--------+
                   |                 |
                   v                 v
           +---------------+   +-----------+
           |POSTURE_METRICS|   |  ALERTS   |
           +---------------+   +-----------+
```

---

# 39. USE CASE DIAGRAM CONTENT

Actor:

```text
User
```

Use cases:

```text
Register
Login
Start Monitoring
Grant Camera Permission
Select Target
Calibrate
Monitor Posture
Receive Visual Alert
Receive Voice Alert
View Recommendation
Stop Monitoring
View Session Report
View Analytics
Change Settings
Enable/Disable Voice Alerts
```

Implementation details such as Redis, FastAPI, MediaPipe, Random Forest, Docker, and MySQL should not be represented as user use cases.

---

# 40. SEQUENCE DIAGRAM CONTENT

```text
User
 |
 | Start Monitoring
 v
React
 |
 | POST /sessions
 v
FastAPI
 |
 | create session
 v
Redis
 |
 | assign/coordinate
 v
ML Worker
 |
 | frame
 v
Monitoring Engine
 |
 | posture/risk
 +--------------------+
 |                    |
 v                    v
Redis              WebSocket
 |                    |
 v                    v
MySQL               React
                       |
                       v
                 Visual + Voice
                       |
                       v
                      User
```

---

# 41. MODULE OWNERSHIP RULES

A module must have one clear responsibility.

```text
CameraView
    -> camera only

FrameManager
    -> frame freshness only

Detector
    -> person detection only

TargetSelector
    -> explicit target choice only

Tracker
    -> identity continuity only

ViewpointEstimator
    -> orientation only

PoseEstimator
    -> landmarks only

PoseValidator
    -> landmark validity only

SittingGate
    -> sitting state only

FeatureExtractor
    -> eight features only

Calibration
    -> baseline collection only

Normalizer
    -> baseline-relative representation

Classifier
    -> posture prediction only

ConfidenceEngine
    -> confidence only

TemporalRiskEngine
    -> temporal risk only

AlertEngine
    -> alert eligibility only

RecommendationEngine
    -> human-readable recommendation only

VoiceAlert
    -> speech delivery only

SessionManager
    -> monitoring lifecycle only

Aggregator
    -> compact metrics only

Repository
    -> database access only

API
    -> HTTP/WebSocket transport only

React components
    -> presentation/user interaction
```

Avoid circular ownership.

---

# 42. WHAT NOT TO DO

Do not:

- create separate front/side ML models;
- rotate engineered scalar features instead of raw landmarks;
- silently switch targets;
- treat missing pose as BAD;
- treat standing as BAD;
- use frame count as time;
- write every frame to MySQL;
- store raw webcam video by default;
- use face recognition unnecessarily;
- put database logic inside React;
- put UI logic inside the ML model;
- put alert logic inside the classifier;
- assume classifier probabilities are perfectly calibrated;
- claim synthetic side-view augmentation is real side-view validation;
- claim 100-user capacity before load testing;
- claim clinical accuracy;
- claim novelty before literature review.

---

# 43. CURRENT STATUS

```text
Phase 0   COMPLETE
Phase 1   COMPLETE
Phase 1.5 COMPLETE
Phase 2   COMPLETE
Phase 3   COMPLETE
Phase 4   NEXT
Phase 5   PENDING
Phase 6   PENDING
Phase 7   PENDING
Phase 8   PENDING
Phase 9   PENDING
Phase 10  PENDING
Phase 11  PENDING
Phase 12  PENDING
Phase 13  PENDING
```

---

# 44. FINAL PROJECT MENTAL MODEL

```text
SEE
 |
 +-- Webcam
 +-- Detection
 +-- Tracking
 +-- Viewpoint
 |
 v
UNDERSTAND
 |
 +-- Pose
 +-- Sitting state
 +-- Features
 |
 v
PERSONALIZE
 |
 +-- Calibration
 +-- Baseline
 |
 v
CLASSIFY
 |
 +-- One unified model
 +-- Five posture classes
 +-- Confidence
 |
 v
STABILIZE
 |
 +-- Temporal smoothing
 +-- Persistence
 +-- Duration
 +-- Recovery
 +-- Risk
 |
 v
COMMUNICATE
 |
 +-- Visual alert
 +-- Browser sound
 +-- Voice message
 +-- Recommendation
 |
 v
SERVE
 |
 +-- React
 +-- FastAPI
 +-- WebSocket
 +-- Redis
 +-- MySQL
 +-- Reports
 +-- Analytics
 |
 v
VALIDATE
 |
 +-- Unit tests
 +-- Integration tests
 +-- E2E
 +-- Load tests
 +-- Research experiments
```

---

# 45. ONE-SENTENCE DESCRIPTION

> **PostureAI is a privacy-conscious real-time webcam-based sitting-posture monitoring platform that uses a unified viewpoint-aware pose representation, eight engineered posture features, one five-class posture model, personal baseline normalization, confidence-aware temporal risk estimation, persistent visual and voice alerts, personalized recommendations, and historical analytics without storing raw webcam video by default.**

---

# 46. AUTHORITATIVE CHANGE LOG

### 2026-09-27

Current architecture explicitly establishes:

- one unified posture model;
- eight final engineered features;
- five ML posture classes;
- same MultiPosture dataset for viewpoint augmentation;
- side-view support through raw 3D landmark transformation and recalculation;
- synthetic side-view clearly separated from real side-view validation;
- viewpoint estimation;
- canonical/viewpoint-aware representation;
- temporal risk must explicitly map five posture classes to severity;
- voice message alerts as a first-class product feature;
- voice preference/settings;
- voice alert frontend module;
- voice-aware WebSocket event;
- `voice_delivered` alert persistence field;
- complete module ownership;
- complete phase roadmap;
- detailed architecture diagrams.

---

# 47. HISTORICAL PROJECT CONTEXT

The original project-context material follows below in full so no historical design detail is lost. The authoritative sections above take precedence where terminology or architecture changed.


---

# PostureAI --- Master Project Context

**Status:** Architecture baseline / implementation specification\
**Purpose:** Single source of truth for the current project context
before implementation and diagram drawing.

> This document records agreed architecture and design decisions.
> Unverified thresholds, capacity numbers, novelty claims, and
> performance figures are explicitly marked as assumptions/TBD and must
> be experimentally validated.

------------------------------------------------------------------------

# 1. Project Overview

## Project

**PostureAI**

## Goal

A web-based, real-time sitting-posture monitoring system for general
users using an ordinary desktop/laptop webcam.

The system should:

-   monitor sitting posture continuously;
-   identify the user-selected person when multiple people are visible;
-   track that person without face recognition;
-   distinguish GOOD, MODERATE, and BAD sitting posture;
-   handle uncertainty, occlusion, missing pose data, and temporary
    target loss;
-   personalize posture interpretation using a user-specific baseline;
-   use prediction confidence and temporal behavior before generating
    risk/alerts;
-   provide posture-specific recommendations;
-   generate persistent session history, reports, and analytics;
-   support approximately 100 concurrent active users architecturally;
-   minimize privacy exposure by not storing raw webcam video by
    default.

## Product boundary

This is a **posture monitoring/decision-support application**, not a
medical diagnostic system.

Do not claim that the system diagnoses disease, musculoskeletal
disorders, or clinically validated injury risk unless separate clinical
validation exists.

------------------------------------------------------------------------

# 2. Core User Flow

``` text
Register / Login
      |
      v
Dashboard
      |
      v
Start Monitoring
      |
      v
Camera Permission / Camera Check
      |
      v
Person Detection
      |
      v
User Selects Target Person
      |
      v
Calibration Check
      |
      +--> First use / major setup change
      |       -> Full calibration (~10–15 s proposed)
      |
      +--> Existing baseline
              -> Quick calibration/check (~3–5 s proposed)
      |
      v
Real-Time Monitoring
      |
      +--> GOOD
      +--> MODERATE
      +--> BAD
              |
              v
       Persistent BAD state
              |
              v
        Alert + Recommendation
      |
      v
Stop Monitoring
      |
      v
Session Finalization
      |
      v
Reports / Analytics
```

The calibration durations are engineering starting points, not
scientifically established optimal values.

------------------------------------------------------------------------

# 3. Technology Stack

  Layer                    Technology
  ------------------------ -------------------------------
  Frontend                 React
  Build tool               Vite
  Styling                  Tailwind CSS
  Backend                  FastAPI
  API                      REST
  Live communication       WebSocket
  Computer vision          OpenCV
  Pose estimation          MediaPipe
  ML classifier            Random Forest
  ML/data processing       Python, Pandas, Scikit-learn
  Live state/queue         Redis
  Persistent DB            MySQL
  Deployment               Docker
  Production entry point   Load balancer / reverse proxy
  Intended scale           \~100 concurrent users

Previously validated development environment:

-   Python 3.11.9
-   MediaPipe 0.10.14
-   OpenCV 4.10.0.84
-   scikit-learn 1.9.0
-   Streamlit 1.60.0
-   Plotly 6.9.0

`mp.solutions` was previously confirmed to work in the correct
environment.

------------------------------------------------------------------------

# 4. High-Level Architecture

``` text
                         USERS
                           |
                           v
                 +--------------------+
                 | React + Vite +      |
                 | Tailwind Frontend   |
                 +---------+----------+
                           |
                      HTTPS / WSS
                           |
                           v
                 +--------------------+
                 | Load Balancer /    |
                 | Reverse Proxy      |
                 +---------+----------+
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
        +----------+  +----------+  +----------+
        | FastAPI1 |  | FastAPI2 |  | FastAPI3 |
        +----+-----+  +----+-----+  +----+-----+
             |             |             |
             +-------------+-------------+
                           |
                           v
                      +---------+
                      | Redis   |
                      +----+----+
                           |
                    ML coordination
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
        +----------+  +----------+  +----------+
        | MLWorker1|  | MLWorker2|  | MLWorker3+|
        +----+-----+  +----+-----+  +----+-----+
             |             |             |
             +-------------+-------------+
                           |
                           v
                Monitoring / Risk Engine
                           |
                 +---------+---------+
                 |                   |
                 v                   v
             WebSocket           Aggregator
                                      |
                                      v
                                    Redis
                                      |
                                      v
                                    MySQL
```

### Important architectural distinction

**FastAPI cluster** handles:

-   authentication;
-   REST APIs;
-   WebSocket connections;
-   session coordination;
-   authorization;
-   interaction with Redis.

**ML worker pool** handles:

-   expensive computer vision;
-   pose processing;
-   feature extraction;
-   model inference;
-   confidence/risk calculations.

**Redis** handles:

-   transient live state;
-   coordination;
-   queues;
-   temporary buffering;
-   shared state between instances.

**MySQL** is the permanent source of truth.

**Load balancer** distributes HTTP/WebSocket connections among FastAPI
instances.

Docker is the deployment/package mechanism; Docker itself is not the
load balancer.

------------------------------------------------------------------------

# 5. Scaling Assumption: 100 Concurrent Users

The architecture is intentionally designed for approximately 100
concurrent users.

Initial conceptual deployment may use:

-   2--3 FastAPI replicas;
-   3+ ML worker replicas.

These are **initial deployment targets, not proven capacity limits**.

The exact number must be established through load testing using:

-   CPU usage;
-   RAM usage;
-   inference latency;
-   ML throughput;
-   queue delay;
-   WebSocket latency;
-   Redis latency;
-   MySQL write throughput;
-   concurrent active sessions.

Do not claim "three workers support 100 users" until it has been
measured.

Avoid Kafka, Kubernetes, service mesh, and unnecessary microservices
unless load testing demonstrates a real need.

------------------------------------------------------------------------

# 6. Frontend Responsibilities

React is the user-facing application.

It contains conceptually:

``` text
pages/
  Login
  Register
  Dashboard
  LiveMonitor
  Reports
  Analytics
  Settings

components/
  CameraView
  PoseOverlay
  PostureStatus
  RiskIndicator
  AlertBanner
  RecommendationCard
  SessionTimer
  Charts

services/
  API client
  WebSocket client
  Authentication

hooks/
  useCamera
  useMonitoring
  useWebSocket

state/
  auth
  monitoring
  settings
```

These are logical modules; exact file organization can change.

## Frontend functions

-   authentication screens;
-   camera permission;
-   camera lifecycle;
-   live monitoring;
-   target selection;
-   calibration UI;
-   posture/risk display;
-   skeleton overlay;
-   recommendations;
-   alerts;
-   reports;
-   analytics;
-   settings;
-   WebSocket reconnection;
-   error states.

------------------------------------------------------------------------

# 7. Browser Camera Architecture

The browser owns the physical webcam.

Conceptually:

``` text
Browser
  |
  +--> getUserMedia()
  |
  v
Camera stream
  |
  v
Frame Manager
```

The backend cannot directly open a remote user's webcam.

The system must respect OS/browser camera permissions.

## Camera states

``` text
INITIALIZING
READY
ACTIVE
DISCONNECTED
ERROR
STOPPED
```

## Permission denied

Do not create an ACTIVE monitoring session.

Show a clear permission/camera message.

## Camera unavailable

Possible causes:

-   camera in use by another application;
-   hardware unavailable;
-   permission revoked;
-   browser/device failure.

Show an error state; never bypass permission.

------------------------------------------------------------------------

# 8. REST and WebSocket Split

## REST

Use REST for relatively stable operations:

``` text
Register
Login
Profile
Settings
Create session
Stop/finalize session
Session history
Reports
Analytics
```

Example conceptual endpoints:

``` text
POST /auth/register
POST /auth/login
GET  /profile
GET  /settings
PUT  /settings
POST /sessions
POST /sessions/{id}/stop
GET  /sessions
GET  /sessions/{id}
GET  /reports/{session_id}
GET  /analytics
```

Exact endpoint names are TBD.

## WebSocket

Use WebSocket for:

-   live posture;
-   confidence;
-   risk;
-   tracking status;
-   recommendations;
-   alerts;
-   connection state.

Example message:

``` json
{
  "posture": "BAD",
  "confidence": 0.91,
  "risk_score": 78,
  "risk_level": "HIGH",
  "tracking_status": "TRACKING",
  "recommendation": "Straighten your back",
  "alert": true
}
```

The final contract should be frozen before frontend/backend integration.

------------------------------------------------------------------------

# 9. Authentication and Authorization

JWT-based authentication is the current direction.

## Rules

-   Passwords are stored as secure hashes, never plaintext.
-   Production uses HTTPS.
-   Production WebSockets use WSS.
-   Never trust arbitrary client-supplied `user_id`.
-   Derive identity from the authenticated token/session.
-   Every session/report/analytics query must verify ownership.
-   User A must never access User B's session.

Authentication means:

> Which account is logged in?

It does **not** mean:

> Which person in the camera is the user?

That second problem is handled by explicit target selection.

------------------------------------------------------------------------

# 10. Monitoring Session vs Login Session

A login session and monitoring session are different.

## Login session

Represents authenticated access to the application.

## Monitoring session

Represents one period of actual posture monitoring.

A monitoring session contains:

``` text
session_id
user_id
started_at
ended_at
duration
posture/risk aggregates
alert statistics
```

------------------------------------------------------------------------

# 11. One Active Monitoring Session Per User

A user should have at most one ACTIVE monitoring session.

Example:

``` text
Tab A -> Session S1 ACTIVE

Tab B -> detects S1 already ACTIVE
       -> reconnects/uses S1
       -> does not create S2
```

This prevents duplicate webcam/ML sessions for one account.

------------------------------------------------------------------------

# 12. Monitoring Runtime Context

Every active monitoring session gets isolated runtime state.

``` text
MonitoringContext
-----------------------------
session_id
frame_buffer
target_track
tracker
tracking_confidence
calibration_state
baseline_profile
pose_state
smoothing_state
risk_state
alert_state
metrics_accumulator
```

Do not use global variables such as:

``` text
current_frame
current_tracker
current_target
current_session
```

because concurrent users would overwrite each other's state.

------------------------------------------------------------------------

# 13. Frame Management

A webcam may produce \~30 FPS.

The ML pipeline can initially target roughly 5--10 processed FPS,
subject to real benchmarking.

Use a **latest-frame buffer**:

``` text
Camera
   |
   v
Latest Frame Buffer
   |
   v
ML takes newest available frame
```

Do not create an unbounded frame queue.

If ML is slower than the camera, stale frames should be dropped rather
than processed later.

The goal is low latency/freshness.

------------------------------------------------------------------------

# 14. Complete ML Pipeline

``` text
Camera Frame
      |
      v
Frame Manager / Latest-Frame Buffer
      |
      v
Person Detection
      |
      v
Target Selection
      |
      v
User Confirmation
      |
      v
Person Tracker
      |
      v
Tracking Confidence
      |
      v
Grace Period
      |
      v
MediaPipe
      |
      v
Pose Validation
      |
      v
Sitting-State Gate
      |
      v
Feature Extraction
      |
      v
Personal Calibration / Baseline Normalization
      |
      v
Random Forest
      |
      v
Prediction Confidence
      |
      v
Confidence-Aware Temporal Risk Modeling
      |
      v
Stable Posture / Risk
      |
      v
Alert Engine
      |
      v
Recommendation Engine
      |
      v
WebSocket -> React
```

------------------------------------------------------------------------

# 15. Person Detection

Possible states:

``` text
NO_PERSON
ONE_PERSON
MULTIPLE_PEOPLE
```

When multiple people are visible, the system must not guess.

It asks the user to explicitly choose the target.

------------------------------------------------------------------------

# 16. Target Selection and Tracking

No face recognition.

Flow:

``` text
Login
  |
  v
Start Monitoring
  |
  v
Detect visible people
  |
  v
User selects/confirms target
  |
  v
Target locked
  |
  v
Tracker follows target
```

Terminology:

-   **Authentication** = account identity.
-   **Target selection** = user chooses which detected person to
    monitor.
-   **Tracking** = follow that selected person.
-   **Face recognition** = intentionally not used.

## Tracking states

``` text
SEARCHING
TRACKING
TEMPORARILY_LOST
TARGET_LOST
AWAITING_CONFIRMATION
RESELECT_REQUIRED
```

## Critical rule

Never automatically switch to another person.

If Person A is selected and Person B crosses in front:

``` text
A selected
  ->
occlusion/uncertainty
  ->
try to recover A
  ->
do not switch to B
```

If A cannot be recovered after the allowed period, request user
confirmation again.

------------------------------------------------------------------------

# 17. Target-Loss Grace Period

A brief disappearance should not immediately end monitoring.

Initial engineering starting point:

**\~2--3 seconds**

This is configurable and must be tested.

If target returns with sufficient continuity:

``` text
TEMPORARILY_LOST -> TRACKING
```

If timeout expires:

``` text
TARGET_LOST -> AWAITING_CONFIRMATION / RESELECT_REQUIRED
```

A target-loss event is not BAD posture.

------------------------------------------------------------------------

# 18. MediaPipe Pose Estimation

MediaPipe supplies pose landmarks.

The project uses these landmarks to derive engineered posture features.

If the target is visible but the required landmarks are insufficient:

``` text
POSE_UNAVAILABLE
```

The system should show something like:

> Please adjust your position so your upper body is visible.

Do not classify missing pose data as BAD.

------------------------------------------------------------------------

# 19. Sitting-State Gate

The product is specifically for sitting posture.

Therefore:

``` text
Pose
 |
 v
Sitting-State Gate
 |
 +--> SITTING ----> classifier
 |
 +--> NOT_SITTING -> pause monitoring
 |
 +--> UNKNOWN ----> insufficient information
```

If the user stands:

``` text
NOT_SITTING
"Not sitting — monitoring paused."
```

Do not report BAD sitting posture.

### Dataset issue

The current training dataset has not yet been conclusively verified as
sitting-only.

This must be investigated before the final sitting-state implementation
is claimed as validated.

------------------------------------------------------------------------

# 20. Training Dataset

Current file:

``` text
data/final_posture_dataset.csv
```

Known characteristics:

-   4,794 rows;
-   no missing values;
-   11 engineered features;
-   `upperbody_label`;
-   `lowerbody_label`;
-   `risk_label`.

Current known risk-label counts:

``` text
BAD       2060
MODERATE  1807
GOOD       927
```

The class distribution is imbalanced and should be considered in
evaluation.

------------------------------------------------------------------------

# 21. Exact Training Features

The Random Forest expects these 11 features:

``` text
1. shoulder_height_difference
2. shoulder_symmetry
3. spine_side_deviation
4. neck_side_tilt
5. hip_alignment_difference
6. forward_head_distance
7. neck_flexion_angle
8. torso_inclination_angle
9. shoulder_forward_displacement
10. hip_flexion_angle
11. spine_curvature_score
```

The live pipeline must generate the exact same features with:

-   same definitions;
-   same units;
-   same transformations;
-   same order.

------------------------------------------------------------------------

# 22. Critical ML Verification Issue

An earlier version of the live `_compute_features` path produced only
four features while the trained Random Forest expected 11.

A later pipeline test succeeded, but this does **not** remove the need
for explicit verification.

Before finalizing:

``` text
Training feature vector
       ==
Live inference feature vector
```

must be verified.

Do not fix a mismatch by arbitrarily changing class thresholds or
forcing predictions.

------------------------------------------------------------------------

# 23. Random Forest

The classifier predicts the posture/risk class:

``` text
GOOD
MODERATE
BAD
```

The classifier is not the entire monitoring system.

The architecture deliberately separates:

``` text
ML Prediction
    |
    v
Confidence
    |
    v
Temporal Risk
    |
    v
Alert
    |
    v
Recommendation
```

------------------------------------------------------------------------

# 24. Model Version Warning

The serialized model was previously created using scikit-learn 1.8.0 and
loaded under 1.9.0, generating an `InconsistentVersionWarning`.

It currently loads/runs.

Do not retrain solely to silence the warning.

For reproducible deployment, eventually pin the verified scikit-learn
version used for the final model/runtime.

------------------------------------------------------------------------

# 25. Personal Baseline Calibration

The main personalization direction is **user-specific baseline
normalization**.

The idea is:

``` text
Current posture feature
       -
User's calibrated baseline
       |
       v
Normalized deviation
```

This accounts for differences in:

-   body proportions;
-   natural sitting posture;
-   camera/setup conditions.

## First-time calibration

Proposed:

``` text
~10–15 seconds
```

The user maintains a comfortable upright reference posture.

Use multiple valid observations and robust aggregation such as a
median/robust average.

Do not rely on one frame.

## Returning user

If a stored baseline exists:

``` text
~3–5 second quick calibration/check
```

Then:

``` text
similar setup -> reuse/update baseline
different setup -> full recalibration
```

Major camera/setup changes may trigger full recalibration.

The exact detection threshold must be experimentally determined.

------------------------------------------------------------------------

# 26. Research Direction 1 --- Personalized Baseline Normalization

Potential research contribution:

> A webcam-based posture monitoring method that normalizes posture
> features relative to a user-specific calibrated baseline.

This is a research direction, not automatically a claim of novelty.

A literature review must determine whether equivalent approaches already
exist.

Do not claim that the method uniquely recovers camera pitch/yaw unless a
real camera-pose-estimation method is implemented and validated.

------------------------------------------------------------------------

# 27. Prediction Confidence

The Random Forest should expose class probabilities rather than only the
hard class label:

``` text
P(GOOD)
P(MODERATE)
P(BAD)
```

Example:

``` text
GOOD      = 0.05
MODERATE  = 0.15
BAD       = 0.80
```

The predicted class is BAD, but the probability distribution retains
uncertainty.

## Probability calibration

Raw classifier probabilities should not automatically be treated as
perfectly calibrated probabilities. If probability values drive the
temporal model, calibration must be evaluated on held-out validation
data. A suitable probability-calibration method may be evaluated using
scikit-learn.

## Confidence definition

``` text
C_t = max(P(GOOD), P(MODERATE), P(BAD))
```

Confidence determines how strongly the current observation is allowed to
change the temporal state.

A low-confidence BAD prediction should not have the same temporal effect
as a high-confidence BAD prediction.

------------------------------------------------------------------------

# 28. Confidence-Aware Temporal Risk Modeling

The temporal layer converts noisy frame-level posture predictions into a
stable **postural-risk state**.

It is **not** a medical injury predictor and must not be interpreted as
a probability of developing a musculoskeletal disorder.

The model uses:

-   posture severity;
-   classifier confidence;
-   previous temporal state;
-   elapsed time;
-   persistence.

## 28.1 Severity from class probabilities

Use:

\[ S_t=P(BAD)\_t+0.5P(MODERATE)\_t \]

This gives approximately:

``` text
GOOD       -> 0
MODERATE   -> 0.5
BAD        -> 1
```

while retaining uncertainty.

The `0.5` weighting is an initial engineering definition, not a
clinically validated severity scale. It should be sensitivity-tested.

## 28.2 Confidence

\[ C_t=`\max`{=tex}(P(GOOD)\_t,P(MODERATE)\_t,P(BAD)\_t) \]

Example:

``` text
[0.05, 0.15, 0.80] -> C_t = 0.80
```

## 28.3 Why confidence is an update weight

An earlier candidate was:

``` text
R_t = alpha * R_(t-1) + (1-alpha) * S_t * C_t
```

This is **not** the preferred final formulation because confidence
should mean "how much should I trust this observation?", not "make the
posture intrinsically less severe".

Therefore define a confidence-weighted observation:

\[ E_t=C_tS_t+(1-C_t)R\_{t-1} \]

High confidence gives the current observation more influence. Low
confidence keeps the system closer to its previous stable state.

## 28.4 Time-aware temporal update

\[ R_t=`\alpha`{=tex}*tR*{t-1}+(1-`\alpha`{=tex}\_t)E_t \]

Use elapsed time rather than a fixed per-frame alpha:

\[ `\alpha`{=tex}\_t=e\^{-`\Delta`{=tex}t/`\tau`{=tex}} \]

where `Delta t` is the elapsed time since the previous valid observation
and `tau` is a configurable temporal time constant.

This avoids making temporal behavior depend on the exact inference FPS.

## 28.5 Final formulation

\[ S_t=P(BAD)\_t+0.5P(MODERATE)\_t \]

\[ C_t=`\max`{=tex}(P(GOOD)\_t,P(MODERATE)\_t,P(BAD)\_t) \]

\[ E_t=C_tS_t+(1-C_t)R\_{t-1} \]

\[ `\alpha`{=tex}\_t=e\^{-`\Delta`{=tex}t/`\tau`{=tex}} \]

\[ R_t=`\alpha`{=tex}*tR*{t-1}+(1-`\alpha`{=tex}\_t)E_t \]

with:

``` text
0 <= R_t <= 1
UI Risk Score = 100 * R_t
```

The UI score is an **algorithmic postural-risk indicator**, not injury
probability.

## 28.6 Required state handling

These are not posture predictions:

``` text
TARGET_LOST
POSE_UNAVAILABLE
NOT_SITTING
UNKNOWN
```

They must not be converted to BAD.

-   `TARGET_LOST`: pause posture-risk updates and request re-selection
    after timeout.
-   `POSE_UNAVAILABLE`: no new posture evidence.
-   `NOT_SITTING`: pause sitting-posture classification and cancel the
    BAD persistence timer.
-   `UNKNOWN`: insufficient information; do not manufacture a posture
    label.

## 28.7 Expected temporal behavior

### Isolated BAD

``` text
GOOD -> GOOD -> BAD -> GOOD -> GOOD
```

Should cause only a temporary risk increase and normally no alert.

### Persistent high-confidence BAD

``` text
BAD 0.92
BAD 0.95
BAD 0.91
BAD 0.94
...
```

Risk should accumulate toward a high postural-risk state and eventually
satisfy the alert condition.

### Low-confidence BAD

A low-confidence observation should have limited influence on the
existing temporal state.

### Oscillating predictions

``` text
BAD -> MODERATE -> BAD -> MODERATE -> BAD
```

The output should be a smoother risk trajectory rather than direct
frame-by-frame alert toggling.

------------------------------------------------------------------------

# 29. Temporal Evaluation

Compare three systems on identical sequences:

### A. Raw prediction

``` text
Random Forest -> immediate posture decision
```

### B. Ordinary temporal smoothing

``` text
Random Forest -> basic temporal smoother
```

### C. Proposed confidence-aware temporal model

``` text
Random Forest
 -> class probabilities
 -> severity
 -> confidence
 -> confidence-weighted observation
 -> elapsed-time temporal update
 -> postural-risk state
```

Measure:

-   false-alert rate;
-   missed persistent-abnormal events;
-   alert latency;
-   number of state transitions;
-   risk-score stability;
-   persistent-BAD detection;
-   behavior under occlusion;
-   behavior under poor visibility;
-   recovery behavior;
-   computational overhead.

Do not invent improvement percentages before experiments.

------------------------------------------------------------------------

# 30. Risk Engine

Risk is a separate layer from Random Forest classification.

Inputs:

``` text
class probabilities
predicted posture
prediction confidence
previous risk
elapsed time
sitting state
tracking state
pose validity
```

Outputs:

``` text
risk_score
risk_level
stable_posture
```

Example only:

``` json
{
  "posture": "BAD",
  "confidence": 0.91,
  "risk_score": 78,
  "risk_level": "HIGH"
}
```

The example is illustrative, not a validated threshold or clinical
result.

## Risk terminology

Use:

``` text
Postural Risk
Ergonomic Risk State
Postural Risk Score
```

Avoid:

``` text
medical risk probability
injury probability
disease probability
diagnosis
```

unless a future clinical validation study actually establishes such a
claim.

## Initial application-level risk bands

A candidate UI mapping is:

``` text
0-39    LOW
40-69   MODERATE
70-100  HIGH
```

These are engineering candidates only and must be tuned/evaluated.

------------------------------------------------------------------------

# 31. Alert Engine

Risk estimation and alert generation are separate.

The alert system responds to **persistent abnormal posture**, not one
BAD frame.

Track:

``` text
bad_posture_start
last_alert_time
alert_count
cooldown
```

## Alert state machine

``` text
NORMAL
   |
   v
PERSISTENT_ABNORMAL
   |
   v
ALERTED
   |
   v
COOLDOWN
   |
   v
NORMAL
```

## Persistence

Initial engineering proposal:

``` text
BAD persistence requirement ~= 10 seconds
```

This is configurable and experimentally evaluated; it is not a medical
threshold.

## Hysteresis

Use separate activation/recovery thresholds to prevent rapid
alert/no-alert oscillation.

Initial candidates:

``` text
activation threshold = 0.70
recovery threshold   = 0.50
```

These values are not medically validated.

## Cooldown

After an alert, do not generate a sound every frame. Use a configurable
reminder/cooldown interval.

------------------------------------------------------------------------

# 32. Recommendation Engine

Recommendations should be based on the detected posture characteristics.

Examples:

``` text
High neck flexion
    -> Keep your head more upright.

High torso inclination
    -> Try to sit more upright.

Forward head displacement
    -> Move your head back toward a neutral position.
```

The final mapping must be based on the actual feature semantics and
tested behavior.

------------------------------------------------------------------------

# 33. Notification and Audio

The application can use:

-   WebSocket alert;
-   browser notification;
-   application sound.

Browser autoplay policies can block sound until user interaction.

Therefore, initialize/enable audio from a user action such as:

``` text
Start Monitoring
```

Limitation:

If the browser is closed or the machine is asleep, live-session browser
alerts cannot be guaranteed.

------------------------------------------------------------------------

# 34. Database Design

## users

``` text
id                PK
name
email             UNIQUE
password_hash
created_at
```

Stores account identity.

## user_settings

``` text
id                PK
user_id           FK -> users.id
notification_enabled
sound_enabled
alert_delay
```

Stores per-user alert preferences.

## sessions

``` text
id                PK
user_id           FK -> users.id
started_at
ended_at
duration
good_percentage
moderate_percentage
bad_percentage
average_risk
max_risk
total_alerts
```

One row per monitoring session.

## posture_metrics

Periodic aggregates, for example approximately one row per minute:

``` text
id                PK
session_id        FK -> sessions.id
timestamp
good_duration
moderate_duration
bad_duration
average_risk
average_confidence
avg_neck_flexion
avg_torso_inclination
```

The aggregation interval is a design/configuration decision.

## alerts

``` text
id                PK
session_id        FK -> sessions.id
timestamp
alert_type
posture
risk_score
message
```

Stores meaningful alert events.

## Relationships

``` text
users
 |
 +---- user_settings
 |
 +---- sessions
           |
           +---- posture_metrics
           |
           +---- alerts
```

------------------------------------------------------------------------

# 35. Reports

No separate `reports` table is required initially.

Reports can be derived from:

``` text
sessions
+
posture_metrics
+
alerts
```

Potential report contents:

-   session duration;
-   GOOD percentage;
-   MODERATE percentage;
-   BAD percentage;
-   average risk;
-   maximum risk;
-   alert count;
-   posture trend;
-   feature statistics;
-   recommendations/summary.

------------------------------------------------------------------------

# 36. Analytics

Derived from historical sessions.

Possible analytics:

-   posture distribution;
-   time in each posture;
-   average risk over time;
-   alert count per session;
-   session duration;
-   posture trends;
-   feature trends.

These are application metrics, not medical outcome measurements.

------------------------------------------------------------------------

# 37. Persistence Pipeline

Normal path:

``` text
Monitoring Engine
       |
       v
Aggregator
       |
       v
Redis
       |
       v
MySQL
```

Do not write every frame/prediction to MySQL.

Persist compact, meaningful aggregates/events.

------------------------------------------------------------------------

# 38. MySQL Failure Handling

If MySQL temporarily fails:

``` text
ML / live monitoring
       |
       +--> continues where possible
       |
       +--> live WebSocket alerts continue
       |
       +--> compact persistence data buffered in Redis
```

When MySQL recovers:

``` text
Redis buffer
     |
     v
Flush
     |
     v
MySQL
```

Redis is a temporary buffer, not the permanent history database.

------------------------------------------------------------------------

# 39. Idempotency

Redis-to-MySQL retries can duplicate records.

Use event IDs or unique constraints where appropriate so a retry does
not create duplicate logical events.

Example:

``` text
event_id UNIQUE
```

The exact schema can be finalized during implementation.

------------------------------------------------------------------------

# 40. Redis Failure

Redis improves coordination and temporary buffering but does not
guarantee zero data loss.

If both Redis and MySQL are unavailable:

-   live monitoring may potentially continue;
-   some persistence can be lost;
-   the application should expose degraded persistence state;
-   recovery behavior must be tested.

Do not claim complete fault tolerance merely because Redis exists.

------------------------------------------------------------------------

# 41. FastAPI Failure

If one FastAPI process crashes:

-   its local in-memory state can be lost;
-   the frontend detects WebSocket disconnect;
-   reconnect logic should run;
-   session recovery/reinitialization must be designed;
-   Redis does not automatically keep the crashed process running.

The load balancer allows traffic to continue through healthy FastAPI
instances, but an active session may still require recovery logic.

------------------------------------------------------------------------

# 42. ML Worker Failure

If an ML worker crashes:

``` text
Worker failure
      |
      v
Session affected
      |
      +--> recover/reassign if implemented
      |
      +--> otherwise temporary monitoring interruption
```

Automatic failover must not be claimed until implemented/tested.

------------------------------------------------------------------------

# 43. Network Disconnect

Suggested lifecycle:

``` text
WebSocket disconnected
       |
       v
TEMPORARILY_DISCONNECTED
       |
       v
Reconnect within timeout?
       |
       +--> YES -> resume
       |
       +--> NO  -> finalize
```

Exact timeout is TBD.

------------------------------------------------------------------------

# 44. Browser Refresh / Close

Treat disconnect as potentially temporary.

``` text
Disconnect
   |
   v
Temporary disconnect
   |
   +--> reconnect -> resume
   |
   +--> timeout -> finalize
```

Explicit Stop is different: it immediately finalizes the monitoring
session.

------------------------------------------------------------------------

# 45. Session State Machine

Suggested states:

``` text
REQUESTED
    |
    v
INITIALIZING
    |
    v
ACTIVE
    |
    +--> TEMPORARILY_DISCONNECTED
    |          |
    |          +--> ACTIVE
    |
    +--> PAUSED
    |
    +--> TARGET_LOST
    |
    +--> AWAITING_CONFIRMATION
    |
    v
COMPLETED
```

These are monitoring states, not posture classes.

Posture states remain:

``` text
GOOD
MODERATE
BAD
```

Other information states include:

``` text
POSE_UNAVAILABLE
NOT_SITTING
UNKNOWN
```

Never map these directly to BAD.

------------------------------------------------------------------------

# 46. Existing Project Modules

Known existing/previous modules:

``` text
src/webcam_pipeline.py
src/confidence_engine.py
src/person_tracker.py
src/progress_analytics.py
src/session_manager.py
src/session_report_engine.py
src/session_risk_engine.py
src/config.py
src/e2e_integration_test.py
```

These are current project assets/logical responsibilities. Final file
boundaries can be reorganized.

## webcam_pipeline.py

Current/previous role:

-   frame processing;
-   pose processing;
-   feature extraction;
-   model inference;
-   confidence;
-   risk;
-   recommendations;
-   alerts;
-   runtime information.

Previously observed output fields:

``` text
frame
posture
confidence
prediction_reliability
risk_score
risk_level
ergonomic_score
uncertainty
tracking_status
neck_flexion
torso_inclination
forward_head_distance
visibility
recommendation
alert
session_duration
fps
inference_time
```

Final architecture should prevent this from becoming an oversized
monolithic module.

## confidence_engine.py

Responsibilities:

-   confidence/reliability;
-   confidence gate;
-   support temporal risk.

It should not own every risk/alert responsibility.

## person_tracker.py

Responsibilities:

-   selected-target tracking;
-   tracking confidence;
-   target-loss state;
-   continuity;
-   no automatic target switching.

## session_manager.py

Responsibilities:

-   create session;
-   lifecycle;
-   one-active-session rule;
-   start/stop;
-   finalization;
-   session status.

## session_risk_engine.py

Responsibilities:

-   temporal risk;
-   persistence;
-   confidence integration;
-   stable risk;
-   BAD duration handling.

## session_report_engine.py

Responsibilities:

-   completed-session aggregation;
-   report preparation.

## progress_analytics.py

Responsibilities:

-   cross-session trends;
-   posture distribution;
-   risk/alert trends.

## config.py

Centralize:

-   tracking grace period;
-   alert delay;
-   alert cooldown;
-   calibration duration;
-   confidence parameters;
-   processing FPS;
-   environment settings;
-   DB/Redis settings.

Avoid magic numbers.

## e2e_integration_test.py

Should eventually test:

``` text
frame
 -> detection
 -> tracking
 -> pose
 -> features
 -> classifier
 -> confidence
 -> risk
 -> alert
 -> session
 -> persistence
```

and eventually Redis/FastAPI/WebSocket integration and failure paths.

------------------------------------------------------------------------

# 47. Suggested ML Module Separation

Target logical structure:

``` text
ml/
  frame_manager.py
  person_detector.py
  person_tracker.py
  pose_estimator.py
  pose_validator.py
  sitting_gate.py
  feature_extractor.py
  calibration.py
  baseline_normalizer.py
  posture_classifier.py
  confidence_engine.py
  temporal_risk_engine.py
  risk_engine.py
  alert_engine.py
  recommendation_engine.py
```

This is a target architecture, not a claim that all these files already
exist.

------------------------------------------------------------------------

# 48. Suggested Backend Structure

``` text
backend/
  app/
    main.py

    api/
      auth.py
      users.py
      settings.py
      sessions.py
      reports.py
      analytics.py
      websocket.py

    services/
      auth_service.py
      session_service.py
      report_service.py
      analytics_service.py
      notification_service.py

    repositories/
      user_repository.py
      session_repository.py
      metrics_repository.py
      alert_repository.py

    models/
      user.py
      user_setting.py
      session.py
      posture_metric.py
      alert.py

    schemas/
      auth.py
      session.py
      posture.py
      report.py

    core/
      security.py
      config.py
      database.py
      redis.py
```

Exact names can change.

------------------------------------------------------------------------

# 49. Suggested Frontend Structure

``` text
frontend/
  src/
    pages/
      Login
      Register
      Dashboard
      LiveMonitor
      Reports
      Analytics
      Settings

    components/
      CameraView
      PoseOverlay
      PostureStatus
      RiskIndicator
      AlertBanner
      RecommendationCard
      SessionTimer
      Charts

    services/
      api
      websocket
      auth

    hooks/
      useCamera
      useMonitoring
      useWebSocket

    state/
      auth
      monitoring
      settings
```

------------------------------------------------------------------------

# 50. Live Monitoring UI

Potential screen:

``` text
+------------------------------------------------+
|                LIVE MONITOR                   |
|                                                |
|  +----------------------+                      |
|  | Webcam               |   TRACKING           |
|  |                      |   Sitting            |
|  |  Pose skeleton       |                      |
|  |                      |   POSTURE: GOOD     |
|  +----------------------+   RISK: LOW         |
|                                                |
|  Recommendation: Sit upright                  |
|                                                |
|  Session: 12:34                                |
|                                                |
|             [ Stop Monitoring ]                |
+------------------------------------------------+
```

When states change, clearly distinguish:

-   tracking;
-   sitting state;
-   posture;
-   risk;
-   alert.

------------------------------------------------------------------------

# 51. UI State Messages

Examples:

``` text
TRACKING:
"Monitoring you"

TEMPORARILY_LOST:
"Your position was temporarily lost. Trying to recover..."

TARGET_LOST:
"Target lost. Please select yourself again."

POSE_UNAVAILABLE:
"Please adjust your position so your upper body is visible."

NOT_SITTING:
"Not sitting — monitoring paused."

LOW CONFIDENCE:
"Posture uncertain — maintaining previous state."
```

------------------------------------------------------------------------

# 52. Privacy Architecture

Default data flow:

``` text
Webcam
   |
   v
Real-time processing
   |
   v
Posture features/results
   |
   v
Aggregated session data
   |
   v
MySQL
```

Not:

``` text
Webcam
   |
   v
Permanent raw-video storage
```

No face recognition and no biometric embeddings are required.

------------------------------------------------------------------------

# 53. Research Problem

Possible formal framing:

> Webcam-based sitting-posture monitoring is affected by user-specific
> anatomical differences, camera placement, visibility, occlusion, and
> noisy frame-level predictions. This project investigates user-specific
> baseline normalization and confidence-aware temporal risk estimation
> to improve the robustness and stability of real-time sitting-posture
> monitoring using a conventional webcam.

This is a proposed research framing. A literature review must establish
the actual research gap.

------------------------------------------------------------------------

# 54. Research Contribution Candidates

## Contribution 1 --- Personalized Baseline Normalization

Investigate whether a personal calibrated baseline improves robustness
across users and camera setups.

## Contribution 2 --- Confidence-Aware Temporal Risk Modeling

Investigate whether combining model confidence with temporal persistence
reduces false alerts and unstable state changes.

## Optional product feature --- Focus/Micro-session mode

A user-facing mode such as:

``` text
25-minute focus session
      |
continuous monitoring
      |
session summary
```

This is primarily an HCI/product feature and should not be forced into
the core ML novelty.

------------------------------------------------------------------------

# 55. Research Experiments

## Experiment A --- Personalization

Compare:

``` text
No baseline normalization
vs
Personal baseline normalization
```

Measure:

-   classification performance;
-   cross-user variation;
-   setup variation;
-   feature stability.

## Experiment B --- Temporal model

Compare:

``` text
Raw prediction
vs
ordinary smoothing
vs
confidence-aware temporal risk
```

Measure:

-   false-alert rate;
-   alert latency;
-   number of state transitions;
-   state stability;
-   robustness under occlusion/noise.

## Experiment C --- Calibration duration

Potential comparison:

``` text
5 sec
10 sec
15 sec
```

Measure baseline stability and downstream performance.

No duration should be called optimal before measurement.

------------------------------------------------------------------------

# 56. Evaluation Metrics

## ML

-   accuracy;
-   precision;
-   recall;
-   F1;
-   confusion matrix;
-   per-class performance.

## Real-time

-   inference latency;
-   end-to-end latency;
-   FPS;
-   p95 latency;
-   alert latency;
-   false-alert rate;
-   state transitions;
-   tracking-loss rate;
-   recovery time.

## Scaling

-   concurrent sessions;
-   CPU;
-   RAM;
-   worker utilization;
-   Redis latency;
-   MySQL write latency;
-   WebSocket latency;
-   queue wait time.

------------------------------------------------------------------------

# 57. Existing Runtime Validation

A dummy webcam pipeline test previously succeeded and returned:

``` text
frame
posture
confidence
prediction_reliability
risk_score
risk_level
ergonomic_score
uncertainty
tracking_status
neck_flexion
torso_inclination
forward_head_distance
visibility
recommendation
alert
session_duration
fps
inference_time
```

The dummy FPS value is not valid evidence for real-world performance.

Real webcam benchmarking is required.

------------------------------------------------------------------------

# 58. Failure Cases the System Must Handle

  Failure                     Required behavior
  --------------------------- -----------------------------------
  Camera permission denied    Do not enter ACTIVE monitoring
  Camera unavailable          Show error
  Camera disconnect           Temporary disconnect/paused state
  No person                   Do not call BAD
  Multiple people             Require explicit target
  Target temporarily lost     Grace period
  Target permanently lost     Require re-selection
  Another person crosses      Never auto-switch
  Insufficient landmarks      POSE_UNAVAILABLE
  User stands                 NOT_SITTING / pause
  Low-confidence prediction   Avoid aggressive state flip
  BAD for short time          No immediate alert
  BAD persists                Alert
  GOOD returns                Reset BAD timer
  Network disconnect          Reconnect/resume or finalize
  Browser closes              Disconnect/recovery timeout
  FastAPI failure             Reconnect/recover
  ML worker failure           Recover/reassign if implemented
  MySQL failure               Buffer compact data in Redis
  Redis failure               Degraded coordination/persistence
  Both Redis + MySQL fail     Persistence loss possible

------------------------------------------------------------------------

# 59. Security Requirements

-   secure password hashing;
-   JWT authentication;
-   authorization on every protected resource;
-   ownership checks;
-   HTTPS;
-   WSS;
-   no arbitrary client user IDs trusted;
-   no raw video storage by default;
-   no face recognition;
-   minimal persisted data;
-   no exposure of internal Redis/MySQL services directly to users.

------------------------------------------------------------------------

# 60. Deployment

## Logical containers

``` text
frontend
fastapi
ml-worker
redis
mysql
reverse-proxy
```

Multiple FastAPI and ML worker replicas can be run.

## Docker Compose direction

Development/initial deployment can use Docker Compose.

Conceptually:

``` text
docker compose
   |
   +-- frontend
   +-- fastapi replicas
   +-- ml-worker replicas
   +-- redis
   +-- mysql
   +-- reverse proxy
```

Example scaling concept:

``` text
docker compose up --scale fastapi=3
```

The exact production hosting environment remains TBD.

------------------------------------------------------------------------

# 61. Deployment Diagram vs Component Diagram

The architecture has information suitable for both:

### Component Diagram

Shows:

-   React;
-   FastAPI;
-   Redis;
-   ML workers;
-   monitoring engine;
-   MySQL;
-   interfaces/dependencies.

### Deployment Diagram

Would show:

-   browser/device;
-   Docker host(s);
-   containers;
-   virtual/physical nodes;
-   network boundaries.

If the report is limited to five diagrams, a component/system
architecture diagram can cover the primary architecture and deployment
information can be represented inside it where useful.

------------------------------------------------------------------------

# 62. UML Diagram Plan

The uploaded GeeksforGeeks reference describes UML as a standardized
visual modeling language for communicating system structure and
behavior. It distinguishes structural and behavioral diagrams. It
describes Use Case diagrams as high-level representations of
functionality and actor interaction without implementation details,
Sequence diagrams as ordered interactions, Component diagrams as
software component relationships, and Deployment diagrams as
physical/virtual deployment. See the uploaded reference around pages
2--8.

## Diagram 1 --- Component/System Architecture

Shows:

``` text
React
Load Balancer
FastAPI replicas
Redis
ML Worker Pool
Monitoring Engine
MySQL
```

Do not overload it with every ML step.

## Diagram 2 --- ML/Posture Monitoring Pipeline

``` text
Webcam
  ↓
Frame Manager
  ↓
Person Detection
  ↓
Target Selection
  ↓
Tracking
  ↓
MediaPipe
  ↓
Pose Validation
  ↓
Sitting-State Gate
  ↓
Feature Extraction
  ↓
Personal Calibration / Baseline Normalization
  ↓
Random Forest
  ↓
Confidence-Aware Temporal Risk Modeling
  ↓
Risk
  ↓
Alert + Recommendation
```

## Diagram 3 --- Use Case Diagram

Actor:

``` text
User
```

High-level use cases:

``` text
Register / Login
Start Monitoring
Monitor Sitting Posture
Receive Alerts & Feedback
View Session Reports
View Analytics
Manage Settings
Stop Monitoring
```

Do not include:

``` text
Redis
FastAPI
MediaPipe
Random Forest
ML Worker
MySQL
Docker
```

Those are implementation details.

## Diagram 4 --- Sequence Diagram

Show chronological live monitoring interaction:

``` text
User
 -> React
 -> FastAPI
 -> Redis
 -> ML Worker
 -> Monitoring Engine
 -> Redis/MySQL
 -> FastAPI
 -> React
 -> User
```

Include REST/WebSocket distinctions.

## Diagram 5 --- ER Diagram

Entities:

``` text
users
user_settings
sessions
posture_metrics
alerts
```

Relationships:

``` text
users
 |
 +-- user_settings
 |
 +-- sessions
       |
       +-- posture_metrics
       |
       +-- alerts
```

------------------------------------------------------------------------

# 63. Why These Five Diagrams

They answer five different questions:

  Diagram                         Question
  ------------------------------- ---------------------------------------
  Component/System Architecture   How is the software organized?
  ML Pipeline                     How does posture analysis work?
  Use Case                        What can the user do?
  Sequence                        In what order do components interact?
  ER                              How is persistent data organized?

Adding every UML type is unnecessary unless the report requirements
demand it.

Potential optional diagrams:

-   State Machine;
-   Activity;
-   Deployment;
-   Class;
-   Communication.

These should only be added if they provide information not already
represented or are explicitly required.

------------------------------------------------------------------------

# 64. Complete Development Roadmap — Authoritative Current Phases

> **Important:** This section is the current authoritative phase roadmap for PostureAI. It supersedes older phase numbering or historical implementation notes elsewhere in this document. Historical material may remain below for traceability, but the current architecture, feature set, model design, and phase status are governed by this roadmap.

## Phase 0 — Environment Standardization — COMPLETE

Goal: establish one reproducible development environment before continuing implementation.

Completed direction:

- Python 3.13.6;
- NumPy 2.4.4;
- Pandas 3.0.1;
- scikit-learn 1.8.0;
- joblib 1.5.3;
- Matplotlib 3.10.8;
- MediaPipe 0.10.33;
- OpenCV-Contrib 5.0.0.93;
- isolated `.venv`;
- `.venv/` excluded from Git;
- pinned `requirements.txt`.

The environment must be verified before final deployment/model release. The exact scikit-learn version used to train and serve the final serialized model must eventually be frozen and tested.

---

## Phase 1 — Dataset Engineering + Baseline ML — COMPLETE

Goal: create a leakage-safe supervised learning baseline from MultiPosture.

Dataset facts:

- 13 participants;
- approximately 4,800 frames;
- MediaPipe Pose Heavy 3D landmarks;
- landmarks normalized relative to hip center;
- subject metadata;
- upper/lower body posture labels;
- `upperbody_label` is the primary supervised target.

Primary posture classes:

```text
TUP = Upright trunk
TLB = Trunk leaning backward
TLF = Trunk leaning forward
TLL = Trunk leaning left
TLR = Trunk leaning right
```

Final engineered features:

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

`subject` is metadata only and must never be used as an ML feature.

Completed artifacts:

```text
data/multiposture_engineered.csv
scripts/train_baseline.py
ml/models/posture_model.joblib
reports/ml/evaluation.json
reports/ml/evaluation.txt
reports/ml/confusion_matrix.png
reports/ml/split_subjects.json
```

Baseline method:

- Random Forest;
- 200 trees;
- `n_jobs=-1`;
- subject-wise train/validation/test split;
- final test subjects held out by subject.

Held-out baseline result:

```text
Test accuracy: 0.975925925925926
Weighted precision: 0.9774626251910524
Weighted recall: 0.975925925925926
Weighted F1: 0.9751074988246377
```

Confusion matrix order:

```text
[TLB, TLF, TLL, TLR, TUP]
```

```text
154   0   0   0   0
  0 284   0   0   1
  0  23  96   0   1
  0   0   0 120   0
  1   0   0   0 400
```

The main observed confusion is `TLL -> TLF`.

Model reload/inference was verified successfully using joblib, including probability output.

---

## Phase 1.5 — Model Comparison + Subject-Wise Cross-Validation — COMPLETE

Goal: avoid selecting the final classifier from a single model assumption.

Candidate models:

1. Logistic Regression;
2. SVM with RBF kernel;
3. Random Forest;
4. Extra Trees;
5. HistGradientBoostingClassifier.

Evaluation protocol:

- keep final test subjects untouched;
- use development subjects only for model comparison;
- 5-fold `GroupKFold` with `subject` as the group;
- scaling inside folds for Logistic Regression/SVM;
- tree models do not require scaling;
- report accuracy, macro P/R/F1, weighted P/R/F1, per-class metrics, mean ± SD, and confusion matrices;
- specifically inspect `TLL` behavior;
- retrain the selected model on all development subjects;
- evaluate once on the untouched final test subjects;
- verify serialized-model reload.

Exact comparison numbers must come from the generated experiment artifacts and must not be invented in this context document.

---

## Phase 2 — Unified Viewpoint Support — COMPLETE

Goal:

> **One dataset → one feature pipeline → one posture model.**

Supported viewpoint states:

```text
FRONT
LEFT_3_4
RIGHT_3_4
LEFT_PROFILE
RIGHT_PROFILE
UNKNOWN
```

Viewpoint determines orientation/left-right interpretation but does not route frames to separate posture models.

Approach:

- start from raw MultiPosture 3D landmarks;
- apply controlled landmark-space yaw transformations;
- candidate rotations: `0°, +45°, -45°, +90°, -90°`;
- recalculate the same eight engineered features after transformation;
- do not rotate already-engineered feature vectors;
- inspect coordinate conventions before assigning left/right signs;
- investigate canonical/body-centered representation using shoulder center, hip center, torso axis, and shoulder axis;
- preserve subject/original-sample/viewpoint/REAL-vs-SYNTHETIC metadata;
- never allow synthetic versions of final-test subjects into training.

Important limitation:

MultiPosture does **not** provide complete real side-view samples. Synthetic viewpoint augmentation is therefore evidence of viewpoint-transformation robustness, not proof of real-world side-view performance.

Completed artifacts include:

```text
data/multiposture_viewpoint_augmented.csv
models/viewpoint_robust_model.joblib
scripts/viewpoint_augmentation.py
scripts/train_viewpoint_model.py
scripts/verify_viewpoint_model.py
reports/ml/viewpoint/final_test_evaluation.json
```

---

## Phase 3 — Real-Time Webcam ML Pipeline — COMPLETE

Goal: run the same unified model on live webcam input without introducing a second front/side model pipeline.

Current architecture:

```text
Webcam
  ↓
Latest Frame Buffer
  ↓
Person Detection
  ↓
Target Selection
  ↓
Target Tracking
  ↓
Viewpoint Estimation
  ↓
MediaPipe Pose
  ↓
Canonical / Viewpoint-Aware Representation
  ↓
Same 8 Features
  ↓
viewpoint_robust_model.joblib
  ↓
Posture + Confidence
```

Required behavior:

- model loaded once;
- latest-frame buffering;
- stale frames dropped;
- selected target identity preserved;
- no silent person switching;
- pose failure explicit;
- viewpoint uncertainty explicit;
- missing pose, target loss, and unknown viewpoint are not classified as BAD.

Person states:

```text
NO_PERSON
ONE_PERSON
MULTIPLE_PEOPLE
```

Tracking states:

```text
SEARCHING
TRACKING
TEMPORARILY_LOST
TARGET_LOST
AWAITING_CONFIRMATION
RESELECT_REQUIRED
```

Browser camera lifecycle:

```text
INITIALIZING
READY
ACTIVE
DISCONNECTED
ERROR
STOPPED
```

The browser owns the physical webcam through `getUserMedia()`. The backend cannot directly open the user's remote webcam.

---

## Phase 4 — Temporal Risk Engine — NEXT / CURRENT IMPLEMENTATION PHASE

Goal:

> Convert frame-level posture predictions into stable, confidence-aware, time-based posture/risk states and justified alerts.

Critical architectural rule:

```text
ML prediction
    ≠
posture risk state
    ≠
alert
```

Flow:

```text
Frame-level prediction
      ↓
Confidence handling
      ↓
Temporal smoothing
      ↓
Persistence
      ↓
Duration
      ↓
Recovery
      ↓
Risk state
      ↓
Alert eligibility
      ↓
Cooldown
```

The engine must be pure and testable. It must not depend on FastAPI, React, Redis, MySQL, browser APIs, or OpenCV.

Input observation should contain at least:

```text
timestamp
posture
confidence
viewpoint
tracking_state
pose_valid
person_present
```

Required behavior:

- configurable confidence threshold;
- confidence-aware temporal smoothing;
- explicit state machine;
- timestamp-based duration rather than frame-count duration;
- persistence before activation;
- recovery confirmation;
- hysteresis where appropriate;
- cooldown after alerts;
- invalid observations handled explicitly;
- session statistics;
- deterministic tests;
- irregular timestamps supported;
- FPS changes must not change the semantic duration logic;
- target loss/recovery and viewpoint changes must not become posture events.

Candidate stable states:

```text
NO_PERSON
POSE_UNAVAILABLE
TRACKING
STABLE_UPRIGHT
STABLE_DEVIATION
RECOVERING
UNKNOWN
```

### Critical Phase 4 correction

The current classifier predicts five posture classes:

```text
TUP
TLB
TLF
TLL
TLR
```

It does **not** directly predict `GOOD`, `MODERATE`, and `BAD`.

Therefore Phase 4 must explicitly define and experimentally justify the mapping from the five posture classes to application-level severity/risk states before any risk-score formula is frozen.

Do not silently reuse an older three-class probability formula.

Candidate engineering parameters such as approximately 10 seconds for persistence or activation/recovery thresholds around `0.70/0.50` are not clinical thresholds and remain configurable experimental parameters until validated.

Planned files:

```text
ml/risk/temporal_risk_engine.py
ml/risk/config.py
tests/test_temporal_risk_engine.py
scripts/experiments/temporal_risk_experiment.py
reports/experiments/temporal_risk_engine_report.md
```

Minimum deterministic tests:

1. stable upright;
2. one noisy bad frame;
3. persistent forward lean;
4. recovery;
5. low-confidence noise;
6. person disappears;
7. unknown viewpoint;
8. cooldown;
9. irregular timestamps;
10. FPS changes;
11. missing observations;
12. viewpoint changes;
13. target recovery/loss;
14. long bad/upright periods;
15. engine reset.

---

## Phase 5 — FastAPI + WebSocket

Goal: expose the ML/risk engine as a real-time backend service.

Implement:

- FastAPI application;
- authentication and authorization;
- monitoring-session lifecycle;
- REST endpoints;
- authenticated WebSocket connections;
- live posture/confidence/risk/tracking/recommendation/alert messages;
- connection/reconnection handling;
- session ownership checks;
- one-active-monitoring-session-per-user enforcement;
- clear API and WebSocket contracts.

REST is for stable operations such as authentication, settings, session creation/finalization, history, reports, and analytics.

WebSocket is for live monitoring state.

Freeze the API/WebSocket contract before frontend integration.

---

## Phase 6 — React + Vite + Tailwind Frontend

Goal: provide the complete user-facing monitoring application.

Pages:

```text
Login
Register
Dashboard
LiveMonitor
Reports
Analytics
Settings
```

Core components:

```text
CameraView
PoseOverlay
PostureStatus
RiskIndicator
AlertBanner
RecommendationCard
SessionTimer
Charts
```

Hooks/services include:

```text
useCamera
useMonitoring
useWebSocket
API client
WebSocket client
Authentication state
```

Implement:

- camera permission/lifecycle;
- target selection;
- calibration UI;
- live monitoring;
- posture/risk display;
- skeleton overlay;
- recommendations;
- alerts;
- reports;
- analytics;
- settings;
- connection/error states;
- WebSocket reconnection behavior.

---

## Phase 7 — Redis + MySQL Persistence and Runtime State

Goal: separate transient live state from durable application history.

Redis responsibilities:

- transient monitoring state;
- queues/coordination;
- temporary buffering;
- shared state across FastAPI/ML workers.

MySQL responsibilities:

- users;
- user settings;
- monitoring sessions;
- compact posture metrics;
- alerts;
- session history;
- report/analytics source data.

Do **not** write every webcam frame to MySQL.

Conceptual tables:

```text
users
user_settings
sessions
posture_metrics
alerts
```

The existing product-level `GOOD/MODERATE/BAD` aggregate fields are legacy concepts and must be reconciled with the current five-class posture model and Phase 4 severity mapping before the final schema is frozen.

---

## Phase 8 — Alerts, Voice Feedback, and Recommendation Engine

Goal: deliver useful feedback only after the temporal engine determines that an alert is justified.

Flow:

```text
Stable risk state
      ↓
Alert eligibility
      ↓
Cooldown check
      ↓
Alert
      ↓
Posture-specific recommendation
      ↓
Optional voice feedback
```

Requirements:

- no alert directly from one noisy frame;
- cooldown enforcement;
- posture-specific recommendations;
- user-configurable notification/sound settings;
- clear separation between risk state and UI alert state;
- no medical diagnosis language.

---

## Phase 9 — Analytics, Session Reports, and Research Evaluation

Goal: turn compact session data into interpretable history and run the scientific evaluation of the system.

Product analytics:

- session duration;
- posture-state durations;
- alert count;
- average/max risk where defined;
- confidence summaries;
- feature summaries;
- historical trends.

Research experiments:

- baseline vs personalized normalization;
- frame-level prediction vs temporal engine;
- temporal ablation;
- confidence ablation;
- calibration duration comparison;
- FPS sensitivity;
- robustness to occlusion;
- lighting changes;
- target crossing/loss;
- camera distance/setup changes;
- different users and sitting positions;
- real webcam validation where labeled ground truth exists.

Potential research questions:

1. Does personal baseline normalization improve robustness across users/camera setups?
2. Does confidence-aware temporal modeling reduce false alerts compared with raw or ordinary-smoothed predictions?
3. How does continuous monitoring relate to established ergonomic assessment approaches such as RULA/REBA?

RULA/REBA are ergonomic assessment methodologies, not medical ground truth.

---

## Phase 10 — Full-System Integration

Goal: integrate the complete stack and verify the end-to-end data path.

Target architecture:

```text
React
  ↕ HTTPS/WSS
FastAPI
  ↕
Redis
  ↕
ML workers / Monitoring Engine
  ↕
MySQL
```

Verify:

- authentication → monitoring session;
- camera → live ML;
- ML → temporal risk;
- risk → alert/recommendation;
- WebSocket → UI;
- session finalization → database;
- reports/analytics → historical data;
- authorization and ownership throughout.

No phase is considered complete merely because the code exists. End-to-end execution and regression testing are required.

---

## Phase 11 — Performance, Failure, and Load Testing

Goal: establish measured reliability and capacity instead of assuming it.

### Failure testing

Test:

- camera permission denial;
- camera disconnect;
- no person;
- multiple people;
- target loss;
- target crossing/occlusion;
- pose loss;
- unknown viewpoint;
- network loss;
- FastAPI restart;
- ML worker restart;
- Redis outage;
- MySQL outage;
- browser refresh;
- duplicate-session attempt;
- stale WebSocket connection.

### Load testing

Progressively test appropriate concurrent active sessions:

```text
10
25
50
75
100
```

Measure at minimum:

- CPU;
- RAM;
- ML inference latency;
- end-to-end latency;
- processed FPS;
- p95/p99 latency;
- WebSocket latency;
- Redis latency;
- MySQL throughput;
- queue depth;
- worker utilization;
- error rate.

The approximately 100-user target is an architectural target until these measurements demonstrate capacity.

---

## Phase 12 — Docker, Deployment, and Production Hardening

Goal: package and deploy the system reproducibly.

Implement:

- Docker images/containers;
- environment-based configuration;
- secret management outside source control;
- production HTTPS/WSS;
- reverse proxy/load balancer;
- health/readiness checks;
- structured logging;
- monitoring/metrics;
- database migration strategy;
- backup/recovery strategy;
- production dependency pinning;
- secure authentication/session configuration.

Docker is a packaging/deployment mechanism; it does not itself provide fault tolerance or scalability.

Deployment must follow measured performance and failure-test results.

---

## Phase 13 — Research Validation, Final Documentation, and Release

Goal: produce the final research-quality system and defensible project report.

Prepare:

- system architecture diagram;
- ML pipeline diagram;
- use-case diagram;
- sequence diagram;
- ER diagram;
- state-machine diagram if useful;
- methodology;
- dataset description;
- feature definitions;
- model-selection methodology;
- viewpoint augmentation methodology;
- real-time inference methodology;
- calibration methodology;
- temporal-risk formulation;
- alert/recommendation logic;
- experiments;
- statistical/evaluation results;
- performance/load-test results;
- limitations;
- reproducibility instructions;
- conclusion;
- future work.

Research claims must be supported by measured experiments and literature review.

Do not claim clinical effectiveness, medical diagnosis, guaranteed accuracy, guaranteed zero false alerts, or novelty without appropriate evidence.

------------------------------------------------------------------------

# 65. Critical Unresolved Items

These must be explicitly resolved or experimentally validated before final claims.

### HIGH PRIORITY

1. Define the final mapping from the five posture classes (`TUP`, `TLB`, `TLF`, `TLL`, `TLR`) to application-level severity/risk states.
2. Define and validate the mathematical risk-score formula.
3. Define and validate the temporal smoothing/persistence/recovery method.
4. Verify the exact eight-feature live inference vector and feature order.
5. Verify viewpoint/canonical representation and left/right sign conventions.
6. Verify the sitting-state gate with appropriate evidence.
7. Validate calibration duration and baseline-normalization benefit.
8. Validate target tracking with multiple people and occlusion.
9. Establish the final scikit-learn training/runtime version.
10. Freeze REST and WebSocket contracts.
11. Reconcile database aggregate fields with the five-class posture model.
12. Load-test the approximately 100-user architecture.
13. Validate real-webcam behavior under realistic lighting, distance, occlusion, and camera placement.
14. Conduct literature review before making novelty claims.
15. Distinguish synthetic viewpoint augmentation results from real-world side-view validation.

### Important evidence boundary

MultiPosture does not contain complete real side-view webcam coverage. Therefore synthetic viewpoint augmentation cannot by itself establish real-world side-view accuracy.

------------------------------------------------------------------------

# 66. Things We Must Not Claim Without Evidence

Do not state:

-   "The system diagnoses musculoskeletal disorders."
-   "The method is medically accurate."
-   "10 seconds is clinically optimal."
-   "Three ML workers definitely support 100 users."
-   "This is the first/novel method" without literature review.
-   "The algorithm guarantees zero false alerts."
-   "Redis guarantees zero data loss."
-   "Docker makes the system fault tolerant."
-   "The model has X% accuracy" without measured results.

------------------------------------------------------------------------

# 67. Final System Mental Model

The complete system should be understood as:

``` text
WHAT THE USER DOES
        |
        v
WHAT THE CAMERA CAN OBSERVE
        |
        v
WHAT POSE ESTIMATION EXTRACTS
        |
        v
WHAT FEATURES ARE COMPUTED
        |
        v
WHAT THE MODEL PREDICTS
        |
        v
HOW CONFIDENT THE MODEL IS
        |
        v
HOW THE RESULT BEHAVES OVER TIME
        |
        v
WHAT STABLE RISK/POSTURE IS PRODUCED
        |
        v
WHEN AN ALERT IS JUSTIFIED
        |
        v
WHAT RECOMMENDATION IS SHOWN
        |
        v
WHAT COMPACT DATA IS STORED
```

This separation is the central architectural principle of PostureAI /
PostureAI.

------------------------------------------------------------------------

# 68. One-Sentence Project Description

> **PostureAI is a scalable webcam-based sitting-posture monitoring
> platform that combines MediaPipe pose estimation, engineered posture
> features, Random Forest classification, user-specific baseline
> normalization, confidence-aware temporal risk estimation,
> persistent-posture alerts, personalized feedback, and historical
> analytics while minimizing storage of raw camera data.**

------------------------------------------------------------------------

# 69. Current Final Architecture Summary

``` text
USER
 |
 v
REACT + VITE + TAILWIND
 |
 | HTTPS / WSS
 v
LOAD BALANCER / REVERSE PROXY
 |
 +--> FASTAPI 1
 +--> FASTAPI 2
 +--> FASTAPI 3
 |
 v
REDIS
 |
 +--> ML WORKER 1
 +--> ML WORKER 2
 +--> ML WORKER 3+
 |
 v
MONITORING ENGINE
 |
 +--> Person Detection
 +--> Target Selection
 +--> Tracking
 +--> MediaPipe
 +--> Pose Validation
 +--> Sitting Gate
 +--> Feature Extraction
 +--> Personal Baseline
 +--> Random Forest
 +--> Confidence
 +--> Temporal Risk
 +--> Alerts
 +--> Recommendations
 |
 +--> Aggregator -> Redis -> MySQL
 |
 v
WEBSOCKET -> REACT -> USER
```

------------------------------------------------------------------------

# 70. Final Architecture Decisions Table

  Item                        Decision
  --------------------------- --------------------------------------
  Product                     PostureAI
  Scope                       Sitting posture
  UI                          React + Vite + Tailwind
  Backend                     FastAPI
  Live transport              WebSocket
  Normal APIs                 REST
  Camera                      Browser webcam
  Pose                        MediaPipe
  ML                          Random Forest
  Classes                     GOOD / MODERATE / BAD
  Target handling             Explicit selection + tracking
  Face recognition            No
  Sitting detection           Sitting-State Gate
  Personalization             User-specific baseline
  Main research direction     Baseline normalization
  Second research direction   Confidence-aware temporal risk
  Live state                  Redis
  ML scaling                  Worker pool
  Permanent DB                MySQL
  Persistence strategy        Aggregated events/metrics
  Raw video storage           No by default
  Auth                        JWT direction
  Deployment                  Docker
  API scaling                 Load balancer + FastAPI replicas
  ML scaling                  ML worker replicas
  Target scale                \~100 concurrent users
  UML diagrams                5 primary diagrams
  Final UI                    React, not Streamlit
  Research claims             Must be literature/experiment backed

------------------------------------------------------------------------

# 71. Document Use

This file is intended to be the **master context/reference** before:

1.  finalizing module contracts;
2.  reorganizing source files;
3.  implementing the production frontend/backend;
4.  drawing the five diagrams;
5.  writing the methodology section;
6.  running experiments;
7.  preparing the research paper.

When a future implementation decision conflicts with this document,
explicitly identify the conflict and decide whether the architecture
should change rather than silently introducing a second architecture.

# 65. Latest Consolidated Project Decisions - 2026-09-27

This section is the current single source of truth where earlier
sections contain candidate values or older formulations.

## 65.1 Final project description

**PostureAI** is a privacy-conscious, webcam-based real-time
sitting-posture monitoring system using computer vision, MediaPipe pose
estimation, engineered posture features, Random Forest classification,
personal baseline normalization, calibrated prediction confidence,
confidence-aware time-based postural-risk modeling, persistent alerts,
personalized feedback, session history, reports, and analytics.

The system is intended for general users. It is not a medical diagnostic
system and does not claim to predict the probability of injury or
disease.

## 65.2 Final architecture

``` text
Users
  |
  v
React + Vite + Tailwind
  |
HTTPS / WSS
  |
  v
Load Balancer / Reverse Proxy
  |
  +--> FastAPI 1
  +--> FastAPI 2
  +--> FastAPI 3
           |
           v
         Redis
           |
           v
      ML Worker Pool
           |
           v
     Monitoring Engine
       |
       +--> WebSocket
       |
       +--> Aggregator -> Redis -> MySQL
```

The exact FastAPI replica count and ML-worker count must be established
by load testing. A 100-user architectural target is not itself a
measured capacity claim.

## 65.3 Responsibility split

### FastAPI cluster

-   authentication;
-   REST APIs;
-   WebSocket connections;
-   session management;
-   lightweight coordination;
-   authorization.

### ML worker pool

-   frame processing;
-   person detection;
-   tracking;
-   MediaPipe pose estimation;
-   feature extraction;
-   calibration/baseline normalization;
-   Random Forest inference;
-   confidence calculation;
-   temporal risk processing;
-   alerts/recommendations where appropriate.

### Redis

-   transient/live state;
-   queues;
-   coordination;
-   temporary buffering;
-   reconnect/session coordination.

Redis is not permanent history and must not be used as an unbounded
webcam-frame store.

### MySQL

Permanent source of truth for:

-   users;
-   settings;
-   sessions;
-   aggregate posture metrics;
-   alerts;
-   historical analytics data.

### Docker

Packages and runs services. Docker itself is not the load balancer.

## 65.4 100-user architecture

Target:

``` text
~100 concurrent active monitoring users
```

The design starts with horizontal FastAPI instances, a load balancer,
Redis, and multiple ML workers.

Do not claim that a fixed number of replicas guarantees 100 users.
Measure:

-   inference time;
-   CPU;
-   RAM;
-   GPU if applicable;
-   effective FPS;
-   p95 latency;
-   WebSocket latency;
-   Redis throughput;
-   MySQL write latency;
-   queue depth/wait time;
-   worker utilization.

## 65.5 Final end-to-end pipeline

``` text
Camera Frame
↓
Latest-Frame Buffer
↓
Person Detection
↓
Target Selection
↓
Person Tracking
↓
Tracking Confidence
↓
Target-Loss Grace Period
↓
MediaPipe Pose Estimation
↓
Pose Validation
↓
Sitting-State Gate
↓
Feature Extraction
↓
Personal Calibration / Baseline Normalization
↓
Random Forest
↓
Class Probabilities
↓
Prediction Confidence
↓
Confidence-Aware Temporal Risk Modeling
↓
Postural Risk Score
↓
Alert State Machine
↓
Recommendation
↓
WebSocket → React
```

## 65.6 Runtime context isolation

Every active monitoring session owns an isolated `MonitoringContext`:

``` text
MonitoringContext
- session_id
- frame_buffer
- target_track
- tracker
- tracking_confidence
- calibration_state
- baseline_profile
- pose_state
- smoothing_state
- risk_state
- alert_state
- metrics_accumulator
```

Do not use global `current_frame`, `current_tracker`, `current_target`,
or `current_session` state across users.

## 65.7 Camera architecture

The browser owns the physical webcam using browser camera APIs. The
backend cannot directly access a remote user's physical webcam.

Flow:

``` text
Start Monitoring
 -> camera permission
 -> camera initialization
 -> ACTIVE monitoring
```

Camera states:

``` text
INITIALIZING
READY
ACTIVE
DISCONNECTED
ERROR
STOPPED
```

Production transport:

``` text
HTTPS / WSS
```

If another application owns the webcam, show camera unavailable; never
bypass OS/browser permissions.

## 65.8 Monitoring/session states

Monitoring states:

``` text
REQUESTED
INITIALIZING
ACTIVE
TEMPORARILY_DISCONNECTED
PAUSED
TARGET_LOST
AWAITING_CONFIRMATION
COMPLETED
```

Posture states:

``` text
GOOD
MODERATE
BAD
```

Observation/data states:

``` text
POSE_UNAVAILABLE
NOT_SITTING
UNKNOWN
```

These must remain distinct. `TARGET_LOST`, `POSE_UNAVAILABLE`, and
`NOT_SITTING` must never automatically become `BAD`.

## 65.9 Multi-person handling

Authentication and visual target identification are different:

``` text
Account identity != visual target identity
```

The user selects which detected person is themselves. A tracker follows
the selected target.

No face recognition or biometric embeddings are required.

If another person crosses in front, never automatically switch targets.
If target identity becomes uncertain, pause and request explicit
re-selection.

Tracker states:

``` text
SEARCHING
TRACKING
TEMPORARILY_LOST
TARGET_LOST
AWAITING_CONFIRMATION
RESELECT_REQUIRED
```

Initial target-loss grace period candidate:

``` text
~2-3 seconds
```

Must be tested rather than treated as a universal value.

## 65.10 Sitting-state gate

``` text
Pose/features
↓
Sitting-State Gate
├── SITTING → classifier
├── NOT_SITTING → pause
└── UNKNOWN → pause
```

Standing is not automatically BAD sitting posture.

The dataset must be checked to establish whether it is actually
sitting-specific.

## 65.11 Frame-management rule

Camera capture may run around 30 FPS while ML inference may run around
5-10 FPS depending on hardware. These are engineering targets, not
measured guarantees.

Use a latest-frame buffer rather than an unbounded queue:

``` text
Camera -> Latest Frame Buffer -> ML
```

Stale frames may be dropped to maintain low latency.

## 65.12 Training dataset

Current dataset:

``` text
data/final_posture_dataset.csv
```

Known:

``` text
4,794 rows
11 engineered features
no missing values
```

Risk-label distribution:

``` text
BAD       2060
MODERATE  1807
GOOD       927
```

Features:

``` text
1. shoulder_height_difference
2. shoulder_symmetry
3. spine_side_deviation
4. neck_side_tilt
5. hip_alignment_difference
6. forward_head_distance
7. neck_flexion_angle
8. torso_inclination_angle
9. shoulder_forward_displacement
10. hip_flexion_angle
11. spine_curvature_score
```

Critical requirement: live inference must reproduce the exact same
feature definitions, order, units, and preprocessing used during
training.

## 65.13 Existing ML environment

Previously validated environment:

``` text
Python 3.11.9
MediaPipe 0.10.14
OpenCV 4.10.0.84
scikit-learn 1.9.0
Streamlit 1.60.0
Plotly 6.9.0
```

A previous model generated an `InconsistentVersionWarning` because it
was serialized under scikit-learn 1.8.0 while runtime was 1.9.0. Pinning
the compatible environment is preferred for reproducibility. Retraining
is not automatically required just because of the warning.

## 65.14 Existing runtime validation

A dummy webcam pipeline previously produced fields including:

``` text
frame
posture
confidence
prediction_reliability
risk_score
risk_level
ergonomic_score
uncertainty
tracking_status
neck_flexion
torso_inclination
forward_head_distance
visibility
recommendation
alert
session_duration
fps
inference_time
```

Dummy FPS is not a production benchmark.

## 65.15 Critical ML verification issue

A previous live `_compute_features` implementation produced only four
features while the model expected 11. The current production pipeline
must be explicitly verified to generate all 11 training features in the
same order and definition.

This should be covered by automated tests before final deployment.

## 65.16 Personal baseline

First-time calibration candidate:

``` text
~10-15 seconds
```

Returning-user quick validation candidate:

``` text
~3-5 seconds
```

Use robust aggregation such as median/robust average of valid
observations.

Potential baseline features:

-   neck flexion;
-   torso inclination;
-   shoulder symmetry;
-   shoulder height difference;
-   forward head distance;
-   other validated posture features.

If current setup is sufficiently similar to stored baseline,
reuse/update it. If substantially different, request recalibration.

These durations are proposed starting values, not experimentally
established optima.

## 65.17 Privacy

Default:

``` text
No raw webcam-video storage
No face recognition
No biometric embeddings
```

Persist only data required for the application/research objectives, such
as aggregate session metrics and alerts.

## 65.18 Database

### users

``` text
id
name
email
password_hash
created_at
```

### user_settings

``` text
id
user_id
notification_enabled
sound_enabled
alert_delay
```

### sessions

``` text
id
user_id
started_at
ended_at
duration
good_percentage
moderate_percentage
bad_percentage
average_risk
max_risk
total_alerts
```

### posture_metrics

``` text
id
session_id
timestamp
good_duration
moderate_duration
bad_duration
average_risk
average_confidence
avg_neck_flexion
avg_torso_inclination
```

### alerts

``` text
id
session_id
timestamp
alert_type
posture
risk_score
message
```

Reports can be derived from sessions + posture_metrics + alerts; a
separate reports table is not required by the current design.

## 65.19 Persistence reliability

Normal:

``` text
Monitoring Engine -> Aggregator -> Redis -> MySQL
```

If MySQL fails:

``` text
live monitoring continues where possible
-> compact persistence data buffered in Redis
-> MySQL recovery
-> retry/flush
```

If Redis and MySQL are both unavailable, zero-loss persistence cannot be
guaranteed.

Use idempotent event IDs so retries do not duplicate alerts or metrics.

## 65.20 Authentication/security

JWT-based authentication is an implementation direction.

Requirements:

-   secure password hashing;
-   server-side authorization;
-   user-owned resource checks;
-   HTTPS/WSS;
-   input validation;
-   parameterized database operations;
-   secrets outside source code;
-   WebSocket authentication;
-   rate limiting where appropriate;
-   never trust arbitrary client `user_id` or client-generated risk
    values.

## 65.21 Frontend

``` text
React
Vite
Tailwind CSS
```

Pages:

``` text
Login
Register
Dashboard
LiveMonitor
Reports
Analytics
Settings
```

Components:

``` text
CameraView
PoseOverlay
PostureStatus
RiskIndicator
AlertBanner
RecommendationCard
SessionTimer
Charts
```

Hooks/services/state:

``` text
useCamera
useMonitoring
useWebSocket
api
websocket
auth
auth state
monitoring state
settings state
```

Streamlit remains useful for ML experiments/debugging but is not the
final UI.

## 65.22 Backend

``` text
backend/app/
  main.py
  api/
    auth.py
    users.py
    settings.py
    sessions.py
    reports.py
    analytics.py
    websocket.py
  services/
    auth_service.py
    session_service.py
    report_service.py
    analytics_service.py
    notification_service.py
  repositories/
    user_repository.py
    session_repository.py
    metrics_repository.py
    alert_repository.py
  models/
    user.py
    session.py
    posture_metric.py
    alert.py
    user_setting.py
  schemas/
    auth.py
    session.py
    posture.py
    report.py
  core/
    security.py
    config.py
    database.py
    redis.py
```

## 65.23 ML modules

``` text
frame_manager.py
person_detector.py
person_tracker.py
pose_estimator.py
pose_validator.py
sitting_gate.py
feature_extractor.py
calibration.py
baseline_normalizer.py
posture_classifier.py
confidence_engine.py
temporal_risk_engine.py
risk_engine.py
alert_engine.py
recommendation_engine.py
```

`webcam_pipeline.py` should orchestrate these modules rather than
becoming a monolith.

## 65.24 Existing modules to reconcile

Existing modules include:

``` text
confidence_engine.py
person_tracker.py
progress_analytics.py
session_manager.py
session_report_engine.py
session_risk_engine.py
config.py
e2e_integration_test.py
src/webcam_pipeline.py
```

`session_risk_engine.py` and the new temporal-risk design must be
consolidated so there is one authoritative implementation.

## 65.25 Alerts and notifications

Alert logic:

``` text
persistent BAD
 -> alert
 -> cooldown
 -> optional reminder
```

Initial candidate persistence:

``` text
~10 seconds
```

Initial candidate hysteresis:

``` text
activation = 0.70
recovery = 0.50
```

These are configurable engineering parameters, not medical thresholds.

Browser sound should be initialized from a user interaction because
browsers can block autoplay.

Browser/OS notification availability depends on browser/device state. A
closed browser or sleeping machine cannot guarantee live-session alerts.

## 65.26 Recommendations

Recommendations are ergonomic feedback, not treatment or diagnosis.

Examples:

``` text
Forward-head posture -> adjust screen height and bring head toward neutral.
Excessive torso inclination -> sit more upright and support the back.
Shoulder asymmetry -> reposition shoulders and check seating position.
```

## 65.27 Reports and analytics

Reports may contain:

-   session duration;
-   GOOD/MODERATE/BAD percentages;
-   average risk;
-   maximum risk;
-   alert count;
-   average confidence;
-   posture-metric summaries;
-   timeline/graphs;
-   recommendations.

Analytics may contain:

-   daily posture distribution;
-   weekly risk trend;
-   alerts per session;
-   average session duration;
-   posture-feature trends;
-   confidence trends.

## 65.28 RULA / REBA positioning

RULA and REBA are established ergonomic assessment methodologies, not
medical diagnostic tests.

They can be used as reference/baseline methods in evaluation, but they
should not automatically be treated as medical ground truth.

Automated RULA/REBA using computer vision and pose estimation already
exists in the literature. Therefore the project must not claim novelty
merely from `MediaPipe + automated ergonomic risk`.

The proposed system is better positioned around continuous sitting
monitoring, personalization, confidence-aware temporal estimation, and
practical persistent alerting, subject to literature verification.

## 65.29 Research questions

### RQ1

Does personal baseline normalization improve posture classification
robustness across users and camera setups?

### RQ2

Does confidence-aware temporal modeling reduce false alerts and unstable
state changes compared with raw frame-level classification and ordinary
temporal smoothing?

### RQ3

How does the proposed continuous monitoring approach relate to
established ergonomic reference methods such as RULA and REBA?

## 65.30 Research baselines

``` text
Rule-based posture thresholds
Random Forest alone
Random Forest + ordinary smoothing
Automated RULA
Automated REBA
Proposed RF + baseline + confidence + temporal model
```

RULA/REBA are comparison/reference frameworks, not automatically ground
truth.

## 65.31 Research evaluation

### Personalization ablation

``` text
without baseline normalization
vs
with baseline normalization
```

### Temporal ablation

``` text
raw RF
vs
ordinary smoothing
vs
confidence-aware temporal model
```

### Confidence ablation

``` text
confidence ignored
vs
confidence used
```

### Calibration-duration experiment

Candidate durations:

``` text
5 s
10 s
15 s
```

### FPS-sensitivity experiment

Verify that elapsed-time temporal behavior remains consistent across
different effective inference rates.

### Robustness tests

-   occlusion;
-   poor lighting;
-   target crossing;
-   temporary target loss;
-   camera movement;
-   camera distance changes;
-   different users;
-   different sitting positions.

## 65.32 Research metrics

ML:

``` text
accuracy
precision
recall
F1
macro F1
confusion matrix
per-class metrics
```

Temporal:

``` text
false-alert rate
alert latency
state-transition count
risk stability
persistent-BAD detection
recovery time
missed-alert rate
```

Real-time:

``` text
inference latency
end-to-end latency
FPS
p50/p95 latency
WebSocket latency
```

Scaling:

``` text
concurrent sessions
CPU
RAM
GPU utilization if applicable
Redis latency
MySQL latency
queue depth
queue wait time
worker utilization
```

## 65.33 Failure cases that must be handled

``` text
camera permission denied
camera unavailable
camera disconnect
network disconnect
browser refresh
browser close
multiple visible people
target temporarily lost
target permanently lost
pose unavailable
user standing
low confidence prediction
occlusion
poor lighting
FastAPI instance failure
ML worker failure
Redis failure
MySQL failure
```

## 65.34 Five final UML diagrams

### Diagram 1 - Component/System Architecture

Shows React, load balancer, FastAPI replicas, Redis, ML worker pool,
monitoring engine, and MySQL.

### Diagram 2 - ML/Posture Monitoring Pipeline

``` text
Webcam
-> Frame Manager
-> Person Detection
-> Target Selection
-> Tracking
-> MediaPipe
-> Pose Validation
-> Sitting Gate
-> Feature Extraction
-> Baseline Normalization
-> Random Forest
-> Confidence
-> Temporal Risk
-> Alert
-> Recommendation
```

### Diagram 3 - Use Case

Actor: User

``` text
Register/Login
Start Monitoring
Monitor Sitting Posture
Receive Alerts & Feedback
View Session Reports
View Analytics
Manage Settings
Stop Monitoring
```

No Redis/FastAPI/MediaPipe/MySQL/Docker implementation details belong in
the use-case diagram.

### Diagram 4 - Sequence

``` text
User -> React -> FastAPI -> Redis -> ML Worker -> Monitoring Engine -> Redis/MySQL -> FastAPI -> React -> User
```

Show chronological REST/WebSocket interactions.

### Diagram 5 - ER

``` text
users
 |
 +-- user_settings
 |
 +-- sessions
       |
       +-- posture_metrics
       |
       +-- alerts
```

## 65.35 What not to add yet

Do not introduce Kafka, Kubernetes, a service mesh, or many independent
microservices unless a concrete requirement or measured bottleneck
justifies them.

For the current target, the following is sufficient as the baseline
architecture:

``` text
React
+
Load Balancer
+
FastAPI replicas
+
Redis
+
ML Worker Pool
+
MySQL
```

## 65.36 Final acceptance checklist

### ML

``` text
[ ] 11-feature inference verified
[ ] preprocessing verified
[ ] model version pinned
[ ] class probabilities verified
[ ] probability calibration evaluated
[ ] sitting-specific dataset status verified
```

### Monitoring

``` text
[ ] camera states
[ ] multi-person target selection
[ ] tracking
[ ] target-loss grace period
[ ] pose validation
[ ] sitting gate
```

### Temporal model

``` text
[ ] severity formula
[ ] confidence formula
[ ] confidence-weighted observation
[ ] elapsed-time alpha
[ ] risk state
[ ] persistence
[ ] cooldown
[ ] hysteresis
```

### Backend/frontend

``` text
[ ] authentication
[ ] authorization
[ ] REST
[ ] WebSocket
[ ] Redis
[ ] MySQL
[ ] React live monitor
[ ] reports
[ ] analytics
[ ] settings
```

### Reliability

``` text
[ ] refresh recovery
[ ] disconnect recovery
[ ] camera failure
[ ] target loss
[ ] ML worker failure
[ ] MySQL failure
[ ] Redis failure
```

### Research

``` text
[ ] literature review
[ ] novelty claim verification
[ ] personalization ablation
[ ] temporal ablation
[ ] confidence ablation
[ ] robustness tests
[ ] RULA/REBA comparison methodology
[ ] limitations
```

## 65.37 Final mental model

``` text
1. SEE
   Webcam + detection + tracking + MediaPipe

2. UNDERSTAND
   Pose validation + sitting gate + feature extraction

3. PERSONALIZE
   Calibration + baseline normalization

4. CLASSIFY
   Random Forest + class probabilities + confidence

5. STABILIZE
   Confidence-aware time-based postural-risk model
   + persistent alert state machine

6. SERVE
   React + FastAPI + Redis + MySQL
   + reports + analytics + notifications
```

The central research path is:

``` text
SEE -> UNDERSTAND -> PERSONALIZE -> CLASSIFY -> STABILIZE
```

and the product architecture serves it through:

``` text
SERVE
```

## 65.38 Single-source-of-truth rule

When implementation decisions change, update this document first.

Keep these explicitly marked as configurable/TBD until measured:

``` text
ML FPS target
FastAPI replica count
ML worker count
calibration duration
target-loss grace period
temporal tau
risk thresholds
alert persistence duration
cooldown duration
risk-level boundaries
```

Never convert a proposed value into a measured claim without validation.

------------------------------------------------------------------------

# 66. Project Summary for Viva / Proposal

> PostureAI is a webcam-based real-time sitting-posture monitoring
> system that uses computer vision and machine learning to classify
> posture as GOOD, MODERATE, or BAD. It detects and tracks a
> user-selected person without face recognition, validates pose quality
> and sitting state, extracts eleven engineered posture features, and
> applies a Random Forest classifier. A user-specific baseline can
> normalize posture features to account for natural differences between
> users and camera setups. Instead of reacting directly to noisy
> frame-level predictions, the system uses class probabilities,
> calibrated confidence, and an elapsed-time temporal model to estimate
> a stable algorithmic postural-risk state. Persistent abnormal posture
> is passed to a separate alert state machine with persistence,
> cooldown, and hysteresis. The platform provides ergonomic
> recommendations, browser/audio alerts, session reports, analytics,
> Redis-backed live coordination/buffering, MySQL persistence, and
> horizontally scalable FastAPI/ML-worker deployment targeted
> architecturally at approximately 100 concurrent users. The research
> evaluation focuses on whether personalization and confidence-aware
> temporal modeling improve robustness and alert stability, while RULA
> and REBA are treated as established ergonomic reference frameworks
> rather than medical ground truth.

------------------------------------------------------------------------

# 67. Final Warning on Scientific Claims

The following distinctions are mandatory in the final report and paper:

``` text
postural risk != injury probability
ergonomic assessment != medical diagnosis
RULA/REBA reference != medical ground truth
MediaPipe pose estimation != research novelty by itself
real-time monitoring != proof of clinical effectiveness
engineering threshold != medical threshold
model confidence != clinical certainty
```

The project can make strong engineering and research claims only where
they are supported by experiments and literature.
