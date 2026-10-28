# PostureAI — Academic Thesis & Research Methodology Report

**Project Title:** PostureAI: A Real-Time Non-Intrusive Sitting Posture Monitoring and Ergonomic Decision Support System Using 3D Computer Vision and Temporal Risk Modeling  
**Academic Classification:** Final Year Engineering Capstone / Master's Thesis  
**Document Code:** `DOC-11-ACADEMIC`  
**Relative Path:** `documents/11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md`  
**Research Date:** October 2026  

---

## Abstract

Prolonged, improper seated posture during computer workstation tasks is a leading primary cause of work-related musculoskeletal disorders (WMSDs), including cervical radiculopathy ("tech neck"), thoracic kyphosis, and chronic lower back pain. Existing interventions rely predominantly on intrusive wearable sensors—which suffer from severe user abandonment—or naive single-frame computer vision heuristics that generate excessive false alerts and fail in multi-person environments. 

This research presents **PostureAI**, an end-to-end, privacy-preserving, non-intrusive sitting posture monitoring and decision-support system operating on standard monocular 2D webcam video. The system captures real-time video frames, extracts 33 3D skeletal landmarks via MediaPipe, normalizes body orientation, and calculates eight biomechanically validated kinematic features. Posture is classified into five discrete spinal-trunk states using an optimized Random Forest classifier. 

To eliminate data leakage, the machine learning pipeline is validated using strict **subject-wise 5-fold cross-validation** across 10 development subjects, achieving a mean **Macro F1 of 0.9797 $\pm$ 0.0205**. On an untouched, held-out test cohort of unseen participants (Subjects 1, 9, 12), the model achieves **97.69% Test Accuracy** and a **Macro F1 of 0.9695**. 

Furthermore, PostureAI introduces:
1. An **Anatomical Target Continuity Tracker** that prevents silent identity switches in multi-person environments without facial recognition.
2. A **Personal Calibration Protocol** that adapts ergonomic thresholds to each individual's neutral anatomical baseline.
3. A **Research-Grade Temporal Risk State Machine** incorporating persistence filtering ($3.0\text{s}$), recovery hysteresis ($5.0\text{s}$), and cooldown locks ($20.0\text{s}$) that effectively eliminates alert fatigue.

The resulting full-stack platform delivers multi-modal visual and vocal biofeedback while ensuring zero raw video retention to uphold user privacy.

---

## 1. Introduction & Theoretical Foundations

### 1.1 Biomechanical Impact of Prolonged Sitting
The biomechanics of seated desk work are characterized by prolonged static contraction of the postural musculature. In a natural, ergonomically sound seated posture:
* The cervical lordosis is maintained, with the center of gravity of the head positioned directly above the cervical vertebrae ($C_1 - C_7$).
* The thoracic spine exhibits a mild, relaxed natural kyphosis ($20^\circ - 40^\circ$).
* The lumbar spine preserves its lordotic curve supported by the pelvis and backrest, minimizing compressive stress on the intervertebral discs.

When cognitive fatigue causes the worker to slump into a forward-leaning posture (`TLF`):
1. **Intradiscal Pressure Escalation:** Intradiscal pressure within the $L_4 - L_5$ disc increases from approximately $100\text{ N/cm}^2$ during relaxed standing to over $185\text{ N/cm}^2$ during unsupported slump sitting (an $85\%$ elevation).
2. **Gravitational Head Torque:** Every inch of anterior head translation multiplies the effective gravitational moment on the cervical extensor muscles (splenius capitis, upper trapezius, levator scapulae), leading to ischemic muscle fatigue, trigger points, and cervicogenic headaches.
3. **Coronal Spinal Asymmetry:** Unilateral leaning (`TLL` or `TLR`) introduces asymmetric shear forces on the lumbar facet joints, accelerating disc degeneration and provoking functional scoliosis.

### 1.2 Clinical Ergonomics Assessment Frameworks (RULA & REBA)
Ergonomists evaluate workstation posture using standardized observational tools:
* **RULA (Rapid Upper Limb Assessment):** Focuses on the neck, trunk, and upper limbs. Assigns risk scores ($1 \to 7$) based on joint angles. Angles of trunk flexion $> 20^\circ$ or neck flexion $> 20^\circ$ immediately escalate the action level.
* **REBA (Rapid Entire Body Assessment):** Extends postural assessment to dynamic loads and lower extremities.

While RULA and REBA provide clinically validated scoring rubrics, they are historically applied via manual paper audits by human ergonomists. PostureAI computationally digitizes these exact biomechanical principles into automated real-time algorithms.

---

## 2. Literature Review & Gap Analysis

```text
+---------------------+-------------------------------+-----------------------------------------------+
| SYSTEM / APPROACH   | PRIMARY TECHNOLOGICAL BASIS   | CRITICAL GAPS & LIMITATIONS IN LITERATURE     |
+---------------------+-------------------------------+-----------------------------------------------+
| Wearable Sensors    | Accelerometers, IMU straps,   | Highly intrusive; requires daily charging;    |
| (Upright Go, etc.)  | piezoelectric chest bands     | high abandonment (>80%); lacks skeletal context.|
+---------------------+-------------------------------+-----------------------------------------------+
| RGB-D / Depth Cams  | Microsoft Kinect, Intel       | Specialized expensive hardware; unavailable   |
| (Prior CV Research) | RealSense time-of-flight      | on standard laptops; bulky desktop footprint. |
+---------------------+-------------------------------+-----------------------------------------------+
| Naive Monocular CV  | 2D OpenPose / YOLO heuristics | Single-frame false alerts on casual actions;  |
| Prototypes          | with static angular cutoffs   | data leakage across frames; no identity lock. |
+---------------------+-------------------------------+-----------------------------------------------+
| PostureAI           | Monocular 2D Webcam + 3D      | Solves all above gaps: Non-intrusive, unified  |
| (This Research)     | BlazePose + Temporal Engine   | ML model, subject-split validation, zero-swap.|
+---------------------+-------------------------------+-----------------------------------------------+
```

### Identified Scientific Gaps Addressed by PostureAI
1. **The Flawed Train/Test Split in Prior Work:** Numerous published papers shuffle video frames randomly across train and test sets. Because consecutive frames from the same human subject share identical morphology and lighting, reported accuracies ($>99\%$) are artificially inflated and collapse when tested on new subjects. PostureAI addresses this by enforcing **strict subject-wise group splits**.
2. **The "Single-Frame Alert" Failure Mode:** Academic prototypes typically evaluate frames in isolation. If a user tilts their head for 1.5 seconds to sip coffee, an alarm sounds. PostureAI resolves this with a **continuous temporal risk state machine**.
3. **Identity Jumping in Multi-Person Scenes:** Previous monocular software fails when a second person enters the background. PostureAI introduces a **combined IoU and anatomical aspect ratio tracker** that guarantees zero silent target hopping.

---

## 3. Research Methodology & Experimental Design

### 3.1 Dataset Architecture (MultiPosture)
The experimental corpus utilizes the MultiPosture 3D dataset comprising 4,794 observations recorded from 13 adult participants performing natural desk postures. Each frame captures 33 3D skeletal landmarks extracted via MediaPipe Pose Heavy, normalized relative to the pelvic midpoint.

### 3.2 Feature Selection Rationale
To ensure fast inference on consumer hardware while eliminating redundant dimensionality, the 99 raw coordinates were mathematically transformed into 8 biomechanical features:
$$\mathbf{F} = \left[ \theta_{\text{head\_pitch}}, \theta_{\text{head\_roll}}, \text{FHD}, \theta_{\text{torso\_pitch}}, \theta_{\text{torso\_tilt}}, \theta_{\text{torso\_rot}}, \text{Asym}_{\text{shoulder}}, \phi_{\text{arm\_elev}} \right]$$

### 3.3 Comparative Experimental Matrix
Five model families were evaluated using 5-Fold Subject-Wise GroupKFold cross-validation across the 10 development subjects ($N = 3,714$ frames):

```text
Cross-Validation Performance Summary (5 Folds across Subjects 2, 3, 4, 5, 6, 7, 8, 10, 11, 13):
1. Random Forest       : Macro F1 = 0.9797 ± 0.0205  (Accuracy = 0.9861) -> SELECTED
2. Extra Trees         : Macro F1 = 0.9782 ± 0.0210  (Accuracy = 0.9856)
3. Hist Gradient Boost : Macro F1 = 0.9729 ± 0.0240  (Accuracy = 0.9814)
4. Support Vector Mach : Macro F1 = 0.9628 ± 0.0270  (Accuracy = 0.9742)
5. Logistic Regression : Macro F1 = 0.9185 ± 0.0380  (Accuracy = 0.9320)
```

---

## 4. Quantitative Results & In-Depth Discussion

### 4.1 Evaluation on Unseen Test Subjects
The selected Random Forest model was retrained on all 10 development subjects and evaluated on the untouched test cohort (Subjects 1, 9, 12; $N = 1,080$ frames):

```text
Final Test Metrics:
* Accuracy           : 0.9769 (97.69%)
* Macro Precision    : 0.9832 (98.32%)
* Macro Recall       : 0.9605 (96.05%)
* Macro F1 Score     : 0.9695 (96.95%)
* Weighted F1 Score  : 0.9761 (97.61%)
```

### 4.2 Confusion Matrix Analysis & Discussion
```text
               PREDICTED
         TLB   TLF   TLL   TLR   TUP
       +-----+-----+-----+-----+-----+
  TLB  | 154 |   0 |   0 |   0 |   0 |
       +-----+-----+-----+-----+-----+
  TLF  |   0 | 284 |   0 |   0 |   1 |
TRUE   +-----+-----+-----+-----+-----+
  TLL  |   0 |  23 |  97 |   0 |   0 |
       +-----+-----+-----+-----+-----+
  TLR  |   0 |   0 |   0 | 120 |   0 |
       +-----+-----+-----+-----+-----+
  TUP  |   1 |   0 |   0 |   0 | 400 |
       +-----+-----+-----+-----+-----+
```

* **Near-Perfect Neutral Upright Detection:** Neutral upright sitting (`TUP`) achieved $99.8\%$ Precision and $99.8\%$ Recall (400 of 401 frames correct). This ensures that workers maintaining good posture are virtually never falsely accused of slouching.
* **The `TLL -> TLF` Asymmetry Coupling:** Exactly 23 frames of `TLL` (Subject 9) were predicted as `TLF`. Biomechanical investigation revealed that when this participant leaned onto their left armrest, they simultaneously slumped their chest forward. Because `torso_pitch` was strongly negative, the decision trees prioritized the slump axis. Importantly, both `TLL` and `TLF` represent severe non-neutral postures mapped to elevated risk ($\text{raw\_risk} = 1.0$), ensuring user protection is fully preserved.

---

## 5. Ethical, Privacy & Workplace Legal Considerations

Implementing computer vision in the workplace raises valid privacy concerns regarding surveillance. PostureAI addresses these concerns through strict **Privacy-by-Design** principles:
1. **Zero Raw Video Storage:** Monocular webcam frames are decoded in transient memory, converted into 33 numerical coordinates, and discarded. Raw video is never saved to disk, logged, or uploaded to cloud servers.
2. **Zero Biometric Facial Recognition:** Identity continuity is maintained solely through bounding box IoU and anatomical aspect ratios. Facial landmarks are used only to estimate head angles and are never embedded into biometric identity vectors.
3. **Client-Controlled Operation:** The user possesses complete control to start, pause, calibrate, or terminate monitoring at will.
4. **GDPR & Privacy Compliance:** All stored database records consist solely of timestamped posture codes and risk scores, completely anonymized from visual surveillance data.

---

## 6. Limitations & Threats to Validity

To preserve academic integrity, the following research boundaries are acknowledged:
* **Synthetic Viewpoint Transformation vs Monocular Self-Occlusion:** Viewpoint robustness was evaluated using mathematical 3D coordinate rotations. While mathematically sound, monocular 2D webcams at true $90^\circ$ profiles suffer from physical self-occlusion (the near shoulder obscures the far shoulder), which requires multi-camera setups or deep occlusion inpainting for complete coverage.
* **Extreme Lighting & Clothing Variations:** Loose, bulky winter clothing or very dark backgrounds can reduce MediaPipe landmark confidence, requiring ambient office lighting for optimal accuracy.

---

## 7. Conclusions & Future Research Directions

**PostureAI** demonstrates that accurate, reliable, real-time posture monitoring is achievable on standard monocular webcams without wearable hardware. By combining a 3D skeletal Random Forest classifier (97.69% test accuracy), personal calibration normalization, target continuity tracking, and a research-grade temporal risk engine, the system delivers practical, non-distracting ergonomic decision support.

### Future Research Directions
1. **Spatio-Temporal Graph Neural Networks (ST-GCN):** Replacing the Random Forest with a lightweight Spatio-Temporal Graph Convolutional Network to model continuous skeletal motion dynamics directly.
2. **Multi-Camera Edge Fusion:** Fusing video feeds from an integrated laptop webcam and an external monitor webcam to eliminate profile self-occlusion.
3. **IoT Smart Desk Actuation:** Interfacing the TemporalRiskEngine with motorized standing desk controllers via Bluetooth to automatically raise the desk to standing height after prolonged sitting intervals.
