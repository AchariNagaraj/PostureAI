# PostureAI — Project Overview, Problem Statement & Scope

**Project Identity:** PostureAI  
**Domain:** Computer Vision, Applied Machine Learning, Ergonomics & Human-Computer Interaction  
**Document Code:** `DOC-01-OVERVIEW`  
**Relative Path:** `documents/01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md`  

---

## 1. Background & Motivation

Over the past two decades, the global workforce has transitioned overwhelmingly into sedentary digital workflows. Knowledge workers, software developers, customer service representatives, data analysts, and students routinely spend between 8 to 12 hours daily seated in front of desktop computers or laptops. 

### 1.1 The Clinical & Ergonomic Reality
Prolonged, uninterrupted seated posture is an established independent risk factor for **Work-Related Musculoskeletal Disorders (WMSDs)**. Biomechanical studies demonstrate that seated postures introduce severe static loading on the spinal column:
* **Forward Head Posture ("Tech Neck"):** The human head weighs approximately 4.5 to 5.5 kg in an anatomically neutral vertical orientation. When the head is flexed forward by 15°, the gravitational load exerted on the cervical spine increases to ~12 kg; at 30° flexion, it reaches ~18 kg; and at 45° to 60° flexion, the effective force exceeds 22 to 27 kg. This chronic strain accelerates cervical disc herniation, suboccipital tension headaches, and myofascial pain syndrome.
* **Thoracic Kyphosis & Slouching (Trunk Leaning Forward):** Prolonged slump sitting eliminates the natural lumbar lordosis, pushes the pelvis into a posterior tilt, increases intradiscal pressure in the L4–L5 and L5–S1 vertebrae by over 40% compared to standing, and compresses internal abdominal viscera, restricting diaphragmatic breathing.
* **Coronal Asymmetry (Trunk Lateral Leaning & Shoulder Elevation):** Asymmetrical sitting habits—such as leaning persistently on one armrest, crossing legs, or craning sideways toward off-center monitors—produce uneven muscular fatigue, unilateral spasm of the quadratus lumborum, and compensatory functional scoliosis.

### 1.2 The Human Behavioral Dilemma
Human proprioception and postural awareness naturally degrade as cognitive focus is consumed by work tasks. Even individuals who know the principles of healthy ergonomics unconsciously slip into slumped, asymmetrical, or forward-tilted postures within 5 to 15 minutes of working. Without objective, gentle feedback, unhealthy postures become muscle memory.

---

## 2. Limitations of Existing Solutions

Prior attempts to solve postural degradation fall into two broad categories, both suffering from acute practical shortcomings:

```text
+----------------------------------------------------------------------------------------------------+
|                                    EXISTING POSTURE SOLUTIONS                                      |
+----------------------------------------------------------------------------------------------------+
|  WEARABLE POSTURE SENSORS                                  RAW CV PROTOTYPES                       |
|  (Clips, Straps, Smart Shirts, Accelerometers)             (Naive Single-Frame Heuristics)         |
|  * High physical intrusiveness; unwearable in summer       * Single-frame false alerts on casual actions   |
|  * Battery charging friction & device maintenance           (taking a drink, scratching, brief stretch)   |
|  * High user abandonment rate (>80% within 3 weeks)        * Fragile to multi-person office environments  |
|  * Lacks contextual skeletal body awareness                * One-size-fits-all rigid thresholds          |
|  * Significant monetary cost ($80 - $250 per device)       * Fragile to webcam tilt & desk height shifts   |
+----------------------------------------------------------------------------------------------------+
```

### 2.1 The Failure of Wearables
* **Intrusiveness & Discomfort:** Users resist wearing physical braces, chest straps, or sensor dongles throughout daily office work.
* **Context Blindness:** A wearable accelerometer attached to the upper back cannot distinguish between a user deliberately leaning forward to inspect a schematic vs slouching passively due to fatigue.
* **Abandonment:** Long-term studies show that wearable biofeedback devices experience severe user drop-off within 14 to 21 days due to the daily burden of charging, pairing, and wearing hardware.

### 2.2 The Pitfalls of Naive Computer Vision Prototypes
* **Instantaneous False Positives (Alert Spam):** Most academic prototypes evaluate camera frames independently. If a user tilts their head for 1.5 seconds to sip coffee or answer a phone call, a naive system immediately fires an audible alarm or intrusive popup. This rapid alert fatigue prompts users to close the application immediately.
* **Multi-Person Office Confusion:** In real-world office and home environments, colleagues, family members, or pets walk behind the monitored worker. Naive vision systems randomly hop bounding boxes and switch targets mid-session, corrupting historical data.
* **Anatomical Rigidity (One-Size-Fits-All):** Every human body possesses unique baseline skeletal angles, torso-to-limb ratios, and desk setups. A system with fixed angular cutoffs (e.g., "head pitch > 15° is bad") misclassifies tall individuals, users with low monitors, or individuals with natural spinal curvatures as perpetually "unhealthy."
* **Viewpoint Brittleness:** Most existing software assumes a perfectly centered front-facing camera. Moving the camera to a laptop side dock or a 3/4 monitor angle completely breaks feature extraction.

---

## 3. The PostureAI Solution & Core Innovations

**PostureAI** overcomes all these limitations by creating a zero-hardware, webcam-powered, intelligent posture monitoring and decision-support ecosystem.

```text
                                        THE POSTUREAI PARADIGM
                                        
   +-----------------------+     +--------------------------+     +-------------------------+
   |  PASSIVE 2D WEBCAM    | --> |  3D CANONICAL SKELETON   | --> |  UNIFIED ML MODEL       |
   |  * Zero wearable tags |     |  * MediaPipe 33 joints   |     |  * 5 discrete postures  |
   |  * Zero hardware cost |     |  * Viewpoint estimation  |     |  * 97.69% test accuracy |
   +-----------------------+     +--------------------------+     +-------------------------+
                                                                               |
                                                                               v
   +-----------------------+     +--------------------------+     +-------------------------+
   |  MULTI-MODAL ALERTS   | <-- |  TEMPORAL RISK ENGINE    | <-- |  PERSONAL CALIBRATION   |
   |  * Toast notifications|     |  * 3s persistence filter |     |  * 10s neutral baseline |
   |  * Voice synthesizer  |     |  * 20s cooldown lock     |     |  * Relative deviation   |
   +-----------------------+     +--------------------------+     +-------------------------+
```

### 3.1 Six Pillars of Technical Innovation
1. **Zero-Hardware Friction:** Operates using standard, ubiquitous 720p or 1080p webcams built into laptops or monitors. No specialized depth sensors (Kinect/RealSense) or wearable accessories are required.
2. **Unified Single-Model Architecture:** Uses a single, highly tuned Random Forest classifier trained on 3D skeletal data that operates consistently across front, 3/4, and profile orientations without requiring multiple fragmented models.
3. **Multi-Person Locking & Zero Silent-Switching:** Includes an interactive target selection mechanism paired with an IoU and anatomical geometry signature tracker. The system guarantees that even when multiple individuals are detected, it **never switches targets silently**.
4. **Adaptive Personal Baseline Normalization:** Features a 10-second calibration wizard that captures the user's natural comfortable upright posture. Subsequent ergonomic evaluations compute *deviations relative to the user's personal baseline*, eliminating setup bias.
5. **Research-Grade Temporal Risk Engine:** Employs a state machine (`NORMAL` -> `WATCH` -> `ACTIVE_RISK` -> `COOLDOWN` -> `RECOVERING`) driven by continuous timestamps. Risky postures must persist continuously past a threshold (`persistence_duration = 3.0s`) before triggering alerts, while a cooldown lock (`20.0s`) prevents alert bombardment.
6. **Actionable Multi-Modal Feedback & Long-Term Analytics:** Delivers non-disruptive visual indicators, natural voice speech synthesis reminders ("Trunk misaligned, please sit upright"), a live skeletal overlay, and historical session analytics with posture transition heatmaps.

---

## 4. Problem Statement & Research Questions

### 4.1 Formal Problem Statement
> *"To design, implement, and evaluate an automated, non-intrusive sitting posture monitoring system using standard monocular webcam video that accurately classifies 3D upper-body postures across diverse viewpoints, adapts to individual anatomical baselines, prevents alert fatigue through temporal risk modeling, and maintains target continuity in multi-person environments without facial recognition."*

### 4.2 Research Questions
* **RQ1 (Classification Fidelity):** Can a unified machine learning model trained on 3D skeletal landmarks reliably classify fine-grained spinal-trunk postures across unseen human subjects?
* **RQ2 (Viewpoint Invariance):** How can 3D skeletal representations be engineered to ensure feature consistency across front, oblique, and lateral webcam orientations without multiplying model complexity?
* **RQ3 (Temporal Stability & False Positive Suppression):** What temporal filtering and hysteresis parameters effectively eliminate false-positive posture alerts during brief casual movements while promptly flagging sustained ergonomic strain?
* **RQ4 (Anatomical Adaptation):** Does relative baseline normalization significantly reduce false alerts compared to fixed static angular thresholds across users of varying heights and desk configurations?
* **RQ5 (Identity Continuity):** How can a system track a specific seated worker amidst multi-person clutter without utilizing privacy-invasive biometric facial recognition?

---

## 5. Scope, Boundary & Non-Goals

To maintain clear scientific and product integrity, PostureAI defines explicit operational boundaries:

### 5.1 In Scope
* Real-time monitoring of seated computer desk users via desktop/laptop webcams.
* Extraction of 33 3D skeletal landmarks using MediaPipe Pose.
* Tracking and distinguishing individual targets in multi-person camera frames.
* Mathematical computation of 8 core biomechanical features and extended ergonomic parameters.
* Supervised classification into 5 upper-body posture categories: `TUP`, `TLF`, `TLB`, `TLL`, `TLR`.
* Personal calibration and deviation tracking.
* Temporal risk assessment and multi-modal alerting (visual toast, audio voice).
* Database persistence of monitoring sessions, posture metrics, and alert incidents.
* Interactive web dashboard displaying live metrics, session summaries, transition heatmaps, and historical trends.

### 5.2 Explicit Non-Goals & Product Boundaries
* **Not a Medical Diagnostic System:** PostureAI is an ergonomic decision-support and awareness tool. It does **not** diagnose medical conditions such as structural scoliosis, cervical radiculopathy, or degenerative disc disease. All warnings and advice are ergonomic suggestions.
* **No Facial Recognition or Biometric Identity Tracking:** Target continuity is maintained solely through bounding box IoU and anatomical skeleton aspect ratios. The system does not capture, store, or process facial biometric embeddings, protecting user privacy.
* **No Raw Video Recording or Cloud Streaming:** Monocular webcam frames are decoded in real-time memory to extract coordinate coordinates; raw video streams are **never** written to disk or transmitted to external third-party cloud servers.
* **Sitting-Specific Scope:** The classifier is purpose-built for seated office postures. Standing, walking, or lying down postures are gated as non-sitting states rather than misclassified as "bad sitting."

---

## 6. Target Audience & Practical Use Cases

```text
+-----------------------+---------------------------------------------------------------------------------+
| TARGET USER GROUP     | PRACTICAL BENEFIT & WORKFLOW IMPACT                                             |
+-----------------------+---------------------------------------------------------------------------------+
| Software Developers   | Operates silently in the background during multi-hour programming marathons,     |
| & Knowledge Workers   | giving gentle voice reminders before neck/back spasms develop.                  |
+-----------------------+---------------------------------------------------------------------------------+
| Remote & Hybrid       | Provides home office workers—who often lack professional ergonomic office       |
| Employees             | chairs—with real-time feedback on makeshift desk setups.                        |
+-----------------------+---------------------------------------------------------------------------------+
| Corporate Wellness    | Aggregates anonymized postural health metrics to audit workstation ergonomics   |
| & HR Departments      | and reduce occupational health insurance claims.                                |
+-----------------------+---------------------------------------------------------------------------------+
| Students & E-Learners | Prevents chronic "tech neck" and study slump during extended online lecture     |
|                       | viewing and homework sessions.                                                  |
+-----------------------+---------------------------------------------------------------------------------+
| Physical Therapists   | Enables patients undergoing rehabilitation to export structured session reports |
| & Ergonomists         | demonstrating their day-to-day sitting compliance.                              |
+-----------------------+---------------------------------------------------------------------------------+
```
