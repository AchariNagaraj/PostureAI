# PostureAI — Executive Summary & Master Documentation Index

**Project Title:** PostureAI — Real-Time Non-Intrusive Sitting Posture Monitoring & Ergonomic Risk Decision Support System  
**Academic Level:** Final Year Engineering Capstone Project  
**Version:** 2.0 (Authoritative Comprehensive Architecture & Documentation)  
**Date:** 2026-10-27  
**Workspace Root:** `d:/FinalYearProject`  
**Documentation Directory:** `d:/FinalYearProject/documents/`  

---

## 1. Executive Summary

**PostureAI** is an end-to-end, privacy-preserving, real-time computer vision and machine learning system engineered to assess, monitor, and guide sitting ergonomics for computer desk workers. By leveraging a single standard 2D webcam, the system extracts 3D skeletal landmarks via MediaPipe, normalizes body orientation, extracts eight biomechanically validated features, classifies posture into five discrete spinal-trunk classes using an optimized Random Forest classifier, and evaluates temporal risk through a state-machine engine that prevents alert fatigue.

### Core Breakthroughs & Architectural Highlights
1. **Unified Multi-Viewpoint Model:** Instead of maintaining separate fragile classifiers for front and side views, PostureAI employs **ONE unified posture model** operating on a canonical, viewpoint-aware feature representation.
2. **Subject-Independent Generalization:** Evaluated using strict subject-wise 5-fold cross-validation across 10 development subjects, achieving a **Macro F1 of 0.9797 ± 0.0205**. On untouched, held-out test subjects (Subjects 1, 9, 12), the model achieves **97.69% Test Accuracy** and **0.9695 Macro F1**.
3. **Zero-Switching Target Continuity Tracker:** Handles multiple individuals in the webcam frame without face recognition. It enables manual target selection and uses combined spatial-IoU and anatomical aspect ratio signatures to guarantee that the system **never silently switches targets** even when bystanders cross the camera field.
4. **Personal Baseline Normalization (Calibration Wizard):** Eliminates false alerts caused by natural variations in spinal curvature, desk height, or camera tilt by establishing a robust median baseline during an initial 10-second calibration routine.
5. **Research-Grade Temporal Risk State Machine:** Distinguishes between instantaneous movement and chronic ergonomic strain. Incorporates configurable temporal accumulation (`persistence_duration = 3.0s`), recovery hysteresis (`recovery_duration = 5.0s`), and alert suppression (`cooldown_duration = 20.0s`).
6. **Production-Ready Full-Stack System:** Modern React 18 + Vite + Tailwind CSS frontend communicating over bi-directional WebSockets (`/ws`) with an asynchronous FastAPI backend backed by SQLAlchemy 2.0 (SQLite/MySQL), Argon2 authentication, session persistence, and comprehensive analytics.

---

## 2. Key Metrics & Project Specifications at a Glance

| Dimension | Specification / Metric Value |
| :--- | :--- |
| **Primary Machine Learning Model** | Random Forest Classifier (`n_estimators=200`, `max_depth=None`, `random_state=42`) |
| **Test Accuracy (Unseen Subjects)** | **97.69%** (Held-out subjects 1, 9, 12) |
| **Test Macro Precision / Recall / F1** | **0.9832** / **0.9605** / **0.9695** |
| **Development Cross-Validation F1** | **0.9797 ± 0.0205** (5-Fold Subject-Wise GroupKFold) |
| **Posture Target Classes** | 5 Upper-Body Classes: `TUP` (Upright), `TLF` (Leaning Forward), `TLB` (Leaning Backward), `TLL` (Leaning Left), `TLR` (Leaning Right) |
| **Temporal Risk States** | 5 Operational States: `NORMAL`, `WATCH`, `ACTIVE_RISK`, `RECOVERING`, `COOLDOWN` |
| **Engineered ML Features** | Exactly 8 biomechanical features (Pitch, Roll, FHD, Torso Pitch, Torso Lateral Tilt, Torso Rotation, Shoulder Asymmetry, Upper Arm Elevation) |
| **Vision & Pose Estimator** | Google MediaPipe PoseLandmarker Lite (`pose_landmarker_lite.task`), 33 3D skeletal landmarks |
| **Streaming Protocol** | Bi-directional WebSocket streaming JSON frames & real-time telemetry |
| **Backend Framework** | FastAPI 0.115.0 + Uvicorn 0.30.6 (Python 3.10+) |
| **Persistence Layer** | SQLAlchemy 2.0 Async (SQLite `postureai.db` / MySQL compatible) |
| **Frontend Framework** | React 18.2 + Vite 5.2 + Tailwind CSS 3.4 + Recharts 2.15 |
| **Authentication & Security** | Argon2 password hashing + itsdangerous TimestampSigner HTTP-only session cookies |

---

## 3. Master Documentation Index

Every aspect of this project is thoroughly documented across twelve specialized, self-contained documentation files located in this `documents/` directory:

| Document File | Title & Scope | Primary Topics Covered |
| :--- | :--- | :--- |
| **[00_EXECUTIVE_SUMMARY_AND_MASTER_INDEX.md](file:///d:/FinalYearProject/documents/00_EXECUTIVE_SUMMARY_AND_MASTER_INDEX.md)** | **Master Index & Executive Overview** | High-level summary, key architectural milestones, performance metrics, navigation matrix. |
| **[01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md](file:///d:/FinalYearProject/documents/01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md)** | **Project Overview, Motivation & Scope** | Ergonomic problem space, musculoskeletal disorders (WMSDs), tech neck, literature gaps, non-intrusive monitoring vision, product boundaries vs medical diagnostics. |
| **[02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md](file:///d:/FinalYearProject/documents/02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md)** | **End-to-End System Architecture & Dataflow** | Tiered component architecture, complete dataflow pipeline, WebSocket protocol, concurrency models, frame lifecycle, Redis/worker scale-out model. |
| **[03_DATASET_AND_FEATURE_ENGINEERING.md](file:///d:/FinalYearProject/documents/03_DATASET_AND_FEATURE_ENGINEERING.md)** | **Dataset Specification & Feature Engineering** | MultiPosture 3D dataset structure (4,794 rows, 102 columns), data validation, mathematical formulas for all 8 core features + extended ergonomic features, correlation matrix. |
| **[04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md](file:///d:/FinalYearProject/documents/04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md)** | **Machine Learning Pipeline & Comparative Benchmarks** | Subject-wise GroupKFold CV, model selection experiments (RF, ExtraTrees, HistGradientBoosting, SVM, LogisticRegression), test evaluation on held-out subjects, confusion matrices. |
| **[05_COMPUTER_VISION_TRACKING_AND_POSE_ESTIMATION.md](file:///d:/FinalYearProject/documents/05_COMPUTER_VISION_TRACKING_AND_POSE_ESTIMATION.md)** | **Computer Vision, Target Tracking & Pose Estimation** | MediaPipe BlazePose pipeline, multi-candidate detection, anatomical signature tracking, strict zero-switching guarantees, viewpoint classification algorithm. |
| **[06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md](file:///d:/FinalYearProject/documents/06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md)** | **Personal Calibration & Temporal Risk Engine** | Personal baseline calibration math, deviation thresholds, rule consensus evaluation, temporal state machine (persistence, cooldown, recovery), alert generation logic. |
| **[07_BACKEND_API_AND_DATABASE_ARCHITECTURE.md](file:///d:/FinalYearProject/documents/07_BACKEND_API_AND_DATABASE_ARCHITECTURE.md)** | **Backend Architecture, REST APIs & Database Schema** | FastAPI routers, WebSocket endpoint handlers, SQLAlchemy models (User, Session, PostureMetric, Alert, UserSetting), database migrations, interval analytics engine (`G_MAX` algorithm). |
| **[08_FRONTEND_ARCHITECTURE_AND_UI_UX.md](file:///d:/FinalYearProject/documents/08_FRONTEND_ARCHITECTURE_AND_UI_UX.md)** | **Frontend Architecture, UI/UX & Client State** | React component tree, Custom hooks (`useMonitoring`, `useCamera`, `useWebSocket`, `useAlertManager`), Pose canvas overlay renderer, Dashboard, LiveMonitor, Reports, Settings pages. |
| **[09_VERIFICATION_TESTING_AND_QUALITY_ASSURANCE.md](file:///d:/FinalYearProject/documents/09_VERIFICATION_TESTING_AND_QUALITY_ASSURANCE.md)** | **Testing, System Verification & QA Hardening** | Unit testing suites, integration tests, temporal engine tests, edge-case failure injection, Vitest frontend tests, performance benchmarks, reliability validations. |
| **[10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md](file:///d:/FinalYearProject/documents/10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md)** | **Setup, Installation & Deployment Guide** | Prerequisites, step-by-step local development setup, environment variables, production deployment with Nginx/Uvicorn, troubleshooting runbook. |
| **[11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md](file:///d:/FinalYearProject/documents/11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md)** | **Academic Thesis & Research Report** | Comprehensive academic report format: Literature review (RULA/REBA comparison), biomechanical theory, quantitative results discussion, privacy & ethics, project limitations, future scope. |
| **[12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md](file:///d:/FinalYearProject/documents/12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md)** | **Complete Source Code & Directory Catalog** | Exhaustive directory listing, every Python/JS/Config file described with line counts, dependencies, exported functions, classes, and architectural roles. |

---

## 4. Reading Paths by Audience

To extract the most value depending on your role or objective:

### Path A: Academic Examiner / Project Evaluator / Viva Defense
1. Start with **[01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md](file:///d:/FinalYearProject/documents/01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md)** for problem formulation and research scope.
2. Read **[03_DATASET_AND_FEATURE_ENGINEERING.md](file:///d:/FinalYearProject/documents/03_DATASET_AND_FEATURE_ENGINEERING.md)** to inspect the biomechanical formulas and data integrity.
3. Review **[04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md](file:///d:/FinalYearProject/documents/04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md)** for experimental rigour and cross-validation results.
4. Deep dive into **[11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md](file:///d:/FinalYearProject/documents/11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md)** for theoretical grounding and clinical ergonomics comparison.

### Path B: Software Architect & Full-Stack Developer
1. Examine **[02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md](file:///d:/FinalYearProject/documents/02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md)** for overall topology and pipeline flow.
2. Study **[07_BACKEND_API_AND_DATABASE_ARCHITECTURE.md](file:///d:/FinalYearProject/documents/07_BACKEND_API_AND_DATABASE_ARCHITECTURE.md)** for the asynchronous backend, WebSockets, and database schema.
3. Review **[08_FRONTEND_ARCHITECTURE_AND_UI_UX.md](file:///d:/FinalYearProject/documents/08_FRONTEND_ARCHITECTURE_AND_UI_UX.md)** for React state management, hooks, and canvas rendering.
4. Consult **[12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md](file:///d:/FinalYearProject/documents/12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md)** for the file-by-file code reference.

### Path C: Machine Learning & Computer Vision Engineer
1. Read **[03_DATASET_AND_FEATURE_ENGINEERING.md](file:///d:/FinalYearProject/documents/03_DATASET_AND_FEATURE_ENGINEERING.md)** for 3D coordinate processing and mathematical derivations.
2. Study **[04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md](file:///d:/FinalYearProject/documents/04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md)** for hyperparameter tuning and model evaluation.
3. Inspect **[05_COMPUTER_VISION_TRACKING_AND_POSE_ESTIMATION.md](file:///d:/FinalYearProject/documents/05_COMPUTER_VISION_TRACKING_AND_POSE_ESTIMATION.md)** for MediaPipe integration and target tracking algorithms.
4. Review **[06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md](file:///d:/FinalYearProject/documents/06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md)** for personal baseline normalization and temporal smoothing.

### Path D: DevOps & Systems Deployment Engineer
1. Follow **[10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md](file:///d:/FinalYearProject/documents/10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md)** for step-by-step setup and environment configuration.
2. Review **[09_VERIFICATION_TESTING_AND_QUALITY_ASSURANCE.md](file:///d:/FinalYearProject/documents/09_VERIFICATION_TESTING_AND_QUALITY_ASSURANCE.md)** to run automated unit and integration tests.
