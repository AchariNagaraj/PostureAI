# PostureAI — Complete Source Code Catalog & File Directory

**Document Code:** `DOC-12-CODEBASE`  
**Relative Path:** `documents/12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md`  
**Workspace Root:** `d:/FinalYearProject`  
**Total Cataloged Subsystems:** 8 Functional Modules (API, Inference, Persistence, Risk, Analytics, Scripts, Frontend, Tests)  

---

## 1. Directory Tree Overview

```text
d:/FinalYearProject/
├── .env                                       # Runtime environment configuration (DATABASE_URL, SECRET_KEY)
├── .env.example                               # Sample environment variable template
├── requirements.txt                           # Python package dependencies
├── alembic.ini                                # Database migration configuration
├── postureai.db                               # Local SQLite development database
├── dataset.csv                                # Reference postural dataset
├── selection_report.md                        # Model comparison & selection markdown report
├── validation_report.md                       # Raw MultiPosture dataset integrity validation report
├── documents/                                 # Central Master Project Documentation (This Folder)
│   ├── 00_EXECUTIVE_SUMMARY_AND_MASTER_INDEX.md
│   ├── 01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md
│   ├── 02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md
│   ├── 03_DATASET_AND_FEATURE_ENGINEERING.md
│   ├── 04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md
│   ├── 05_COMPUTER_VISION_TRACKING_AND_POSE_ESTIMATION.md
│   ├── 06_CALIBRATION_AND_TEMPORAL_RISK_ENGINE.md
│   ├── 07_BACKEND_API_AND_DATABASE_ARCHITECTURE.md
│   ├── 08_FRONTEND_ARCHITECTURE_AND_UI_UX.md
│   ├── 09_VERIFICATION_TESTING_AND_QUALITY_ASSURANCE.md
│   ├── 10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md
│   ├── 11_RESEARCH_METHODOLOGY_AND_ACADEMIC_REPORT.md
│   └── 12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md
├── data/                                      # Engineered and augmented CSV datasets
│   ├── multiposture_engineered.csv            # 8-feature engineered dataset (4,794 rows)
│   └── posture_extended_dataset.csv           # 12-feature extended research dataset
├── ml/                                        # Core Machine Learning & Backend Logic
│   ├── api/                                   # FastAPI Routers & Endpoints
│   │   ├── app.py                             # Root FastAPI ASGI app & WebSocket (/ws) endpoint
│   │   ├── analytics_router.py                # REST endpoints for KPIs, charts, and reports
│   │   └── auth_router.py                     # Argon2 authentication, registration & session cookies
│   ├── inference/                             # Computer Vision & Real-Time Inference
│   │   ├── inference_service.py               # InferenceEngine coordinator & model runner
│   │   ├── feature_extractor.py               # 8-feature formulas, CalibrationBaseline & rules
│   │   ├── pose_processor.py                  # MediaPipe PoseLandmarker Lite & Base64 decoder
│   │   ├── target_tracker.py                  # Multi-candidate tracking & zero-switch safety
│   │   └── viewpoint_estimator.py             # Skeletal yaw angle differential estimator
│   ├── models/                                # Trained Model Binaries & Vision Assets
│   │   ├── selected_development_model.joblib  # Trained Random Forest classifier binary (2.65 MB)
│   │   ├── posture_model.joblib               # Production deployed Random Forest binary
│   │   └── pose_landmarker_lite.task          # MediaPipe BlazePose model asset (5.78 MB)
│   ├── persistence/                           # Asynchronous Database Tier
│   │   ├── db.py                              # Async SQLAlchemy engine & sessionmaker
│   │   ├── models.py                          # Declarative relational schema (User, Session, etc.)
│   │   ├── repositories.py                    # Low-level CRUD database query repository
│   │   └── service.py                         # Non-blocking async event persistence service
│   ├── risk/                                  # Temporal Postural Risk Engine
│   │   ├── risk_config.py                     # TemporalRiskConfig dataclass & parameter bounds
│   │   └── temporal_risk_engine.py            # Temporal state machine (persistence, cooldown, etc.)
│   ├── analytics/                             # Advanced Statistical Analytics Service
│   │   └── service.py                         # Gap-filtered duration math (G_MAX) & transition matrix
│   └── tests/                                 # Comprehensive Backend Integration Test Suite (14 files)
├── scripts/                                   # Development, Training & Evaluation Utility Scripts
│   ├── generate_enriched_dataset.py           # Feature engineering & dataset synthesis
│   ├── model_comparison_cv.py                 # 5-fold GroupKFold benchmark across 5 models
│   ├── train_baseline.py                      # Subject-wise training script for Random Forest
│   ├── temporal_risk_monitor.py               # CLI temporal risk simulation script
│   └── webcam_inference.py                    # OpenCV local webcam testing harness
├── reports/                                   # Model Comparison & Evaluation Artifacts
│   └── ml/                                    # Confusion matrices, JSON metrics, fold splits
└── frontend/                                  # React 18 + Vite Web Application
    ├── package.json                           # NPM dependencies & build scripts
    ├── vite.config.ts                         # Vite server configuration & API reverse proxy
    ├── tailwind.config.cjs                    # Tailwind dark-mode design system tokens
    ├── src/
    │   ├── App.jsx                            # React root router & ProtectedRoute wrappers
    │   ├── main.jsx                           # DOM mount bootstrap
    │   ├── pages/                             # Route View Components
    │   │   ├── LiveMonitor.jsx                # Real-time monitoring hub & canvas overlay
    │   │   ├── Dashboard.jsx                  # Aggregate KPI cards, donut chart, heatmap
    │   │   ├── Reports.jsx                    # Session-specific timeline audit inspector
    │   │   ├── Analytics.jsx                  # Historical compliance trends
    │   │   ├── Settings.jsx                   # User preferences & voice toggle
    │   │   ├── Login.jsx                      # User sign-in form
    │   │   └── Register.jsx                   # Account registration form
    │   ├── components/                        # Reusable Visual & Functional Components (20 files)
    │   │   ├── PoseOverlay.jsx                # 2D Canvas kinematic skeletal renderer
    │   │   ├── CameraView.jsx                 # HTML5 video element & canvas frame grabber
    │   │   ├── CalibrationCard.jsx            # 10-second calibration countdown wizard
    │   │   ├── TargetSelector.jsx             # Multi-person interactive selection pills
    │   │   ├── AlertBanner.jsx                # Animated toast alert notification
    │   │   ├── PostureStatus.jsx              # Status pill badge & anatomical checks
    │   │   ├── RiskIndicator.jsx              # Continuous risk score gradient bar
    │   │   ├── RecommendationCard.jsx         # Actionable posture correction tips
    │   │   ├── SessionTimer.jsx               # Active session elapsed time counter
    │   │   ├── ViewpointIndicator.jsx         # Camera orientation indicator pill
    │   │   ├── PostureDistributionChart.jsx   # Donut & bar charts via Recharts
    │   │   ├── TransitionHeatmap.jsx          # Color-coded transition matrix
    │   │   ├── SessionTimelineChart.jsx       # Risk timeline series chart
    │   │   └── KpiCard.jsx                    # Executive metric card container
    │   ├── hooks/                             # Custom React Hooks
    │   │   ├── useMonitoring.js               # Conductor hook connecting camera & WebSocket
    │   │   ├── useCamera.js                   # getUserMedia webcam hardware lifecycle
    │   │   ├── useWebSocket.js                # Bi-directional WebSocket streaming
    │   │   ├── useAlertManager.js             # Active alert throttling & dismissal
    │   │   └── useVoiceAlert.js               # Native Web Speech synthesis hook
    │   ├── state/                             # Context Providers
    │   │   ├── AuthContext.jsx                # User identity & authentication state
    │   │   └── store.js                       # UI context & global toast banners
    │   └── utils/
    │       └── postureLabels.js               # Visual styling tokens & label mapping
```

---

## 2. File-by-File Technical Specification

### 2.1 Backend Core Subsystem (`ml/api/`)

#### [ml/api/app.py](file:///d:/FinalYearProject/ml/api/app.py)
* **Lines of Code:** 287 lines | **Role:** Central application gateway & WebSocket coordinator.
* **Dependencies:** `fastapi`, `uvicorn`, `InferenceEngine`, `PoseProcessor`, `TargetTracker`, `persistence_service`.
* **Exported Symbols:** `app: FastAPI`, `websocket_endpoint()`, `root()`, `health()`.
* **Description:** Initializes database tables on startup. Handles the bi-directional `/ws` WebSocket endpoint, orchestrating frame decoding, multi-person tracking, calibration messaging, model inference, temporal risk scoring, and non-blocking asynchronous persistence.

#### [ml/api/analytics_router.py](file:///d:/FinalYearProject/ml/api/analytics_router.py)
* **Lines of Code:** 91 lines | **Role:** Authenticated REST analytics service.
* **Dependencies:** `fastapi`, `analytics_service`, `get_current_user`.
* **Exported Routes:**
  * `GET /api/analytics/summary`: Aggregate monitoring KPIs (duration, compliance %, alert count).
  * `GET /api/analytics/postures`: Posture observation counts, durations, and transition matrix.
  * `GET /api/analytics/sessions`: Paginated list of user sessions.
  * `GET /api/analytics/sessions/{id}`: Detailed metric series and timeline for a specific session.
  * `GET /api/reports/sessions/{id}`: Structured inspection report payload.

#### [ml/api/auth_router.py](file:///d:/FinalYearProject/ml/api/auth_router.py)
* **Lines of Code:** 103 lines | **Role:** Authentication & security management.
* **Dependencies:** `argon2.PasswordHasher`, `itsdangerous.TimestampSigner`, `pydantic`.
* **Exported Routes:**
  * `POST /api/auth/register`: Creates new user account; hashes password via Argon2; sets signed cookie.
  * `POST /api/auth/login`: Verifies email and password hash; sets session cookie.
  * `POST /api/auth/logout`: Clears session cookie.
  * `GET /api/auth/me`: Returns currently authenticated user profile.
  * Dependency: `get_current_user`: Validates signed session cookie and retrieves `User` model.

---

### 2.2 Computer Vision & Inference Subsystem (`ml/inference/`)

#### [ml/inference/feature_extractor.py](file:///d:/FinalYearProject/ml/inference/feature_extractor.py)
* **Lines of Code:** 439 lines | **Role:** Mathematical feature extraction, calibration baseline, and rule engine.
* **Exported Functions & Classes:**
  * `head_pitch()`, `head_roll()`, `forward_head_displacement()`, `torso_pitch()`, `torso_lateral_tilt()`, `torso_rotation()`, `shoulder_asymmetry()`, `upper_arm_elevation()`.
  * `craniovertebral_angle()`, `neck_lateral_tilt()`, `shoulder_diff()`, `shoulder_tilt_angle()`.
  * `FEATURE_FUNCS: List[Callable]`: Ordered 8-feature execution array.
  * `CalibrationBaseline`: Collects valid frames and computes robust median reference profile.
  * `evaluate_posture_rules()`: Derives consensus posture status (`GOOD` / `MODERATE` / `BAD`) using personal baseline deviations.

#### [ml/inference/target_tracker.py](file:///d:/FinalYearProject/ml/inference/target_tracker.py)
* **Lines of Code:** 443 lines | **Role:** Multi-person target continuity and zero-switch safety tracker.
* **Exported Functions & Classes:**
  * `calculate_iou()`: Computes Intersection over Union of normalized bounding boxes.
  * `extract_geometry_signature()`: Computes anatomical aspect ratio vector.
  * `TargetTracker`: Maintains target identity, matches candidates, manages 10-frame grace periods, and enforces manual reselection when targets are lost.

#### [ml/inference/pose_processor.py](file:///d:/FinalYearProject/ml/inference/pose_processor.py)
* **Lines of Code:** 122 lines | **Role:** MediaPipe PoseLandmarker wrapper & frame decoder.
* **Exported Class:** `PoseProcessor`: Decodes Base64 JPEG buffers, converts BGR to RGB, and executes Google's MediaPipe `pose_landmarker_lite.task` to extract 33 3D skeletal landmarks across up to 5 simultaneous persons.

#### [ml/inference/inference_service.py](file:///d:/FinalYearProject/ml/inference/inference_service.py)
* **Lines of Code:** 203 lines | **Role:** High-level inference engine coordinator.
* **Exported Class:** `InferenceEngine`: Loads trained Random Forest binary (`posture_model.joblib`), manages calibration states (`IDLE`, `CALIBRATING`, `CALIBRATION_COMPLETE`), executes model probability predictions, and interfaces with the `TemporalRiskEngine`.

#### [ml/inference/viewpoint_estimator.py](file:///d:/FinalYearProject/ml/inference/viewpoint_estimator.py)
* **Lines of Code:** 50 lines | **Role:** 3D skeletal orientation estimator.
* **Exported Function:** `estimate_viewpoint()`: Calculates shoulder horizontal width $W_x$ and depth differential $\Delta z$ to classify user orientation into `FRONT`, `LEFT_3_4`, `RIGHT_3_4`, `LEFT_PROFILE`, or `RIGHT_PROFILE`.

---

### 2.3 Temporal Risk Engine Subsystem (`ml/risk/`)

#### [ml/risk/temporal_risk_engine.py](file:///d:/FinalYearProject/ml/risk/temporal_risk_engine.py)
* **Lines of Code:** 234 lines | **Role:** Research-grade temporal risk state machine.
* **Exported Classes:**
  * `RiskState(enum.Enum)`: `NORMAL`, `WATCH`, `ACTIVE_RISK`, `RECOVERING`, `COOLDOWN`.
  * `TemporalRiskEngine`: Continuous timestamp-driven risk accumulator. Enforces persistence filtering ($3.0\text{s}$), recovery hysteresis ($5.0\text{s}$), cooldown suppression ($20.0\text{s}$), and emits structured alert payloads.

#### [ml/risk/risk_config.py](file:///d:/FinalYearProject/ml/risk/risk_config.py)
* **Lines of Code:** 33 lines | **Role:** Configuration dataclass.
* **Exported Class:** `TemporalRiskConfig`: Declares all configurable parameters (durations, risk mappings, thresholds, invalid states).

---

### 2.4 Asynchronous Persistence Subsystem (`ml/persistence/`)

#### [ml/persistence/models.py](file:///d:/FinalYearProject/ml/persistence/models.py)
* **Lines of Code:** 96 lines | **Role:** Declarative relational database models.
* **Exported Models:** `User`, `Session`, `PostureMetric`, `Alert`, `UserSetting`.

#### [ml/persistence/db.py](file:///d:/FinalYearProject/ml/persistence/db.py)
* **Lines of Code:** 32 lines | **Role:** Asynchronous database engine setup.
* **Exported Objects:** `engine`, `AsyncSessionLocal`, `Base`.

#### [ml/persistence/repositories.py](file:///d:/FinalYearProject/ml/persistence/repositories.py)
* **Lines of Code:** 120 lines | **Role:** Low-level async database CRUD operations.
* **Exported Functions:** `create_session()`, `finish_session()`, `add_metric()`, `add_alert()`, `get_user_settings()`.

#### [ml/persistence/service.py](file:///d:/FinalYearProject/ml/persistence/service.py)
* **Lines of Code:** 85 lines | **Role:** Non-blocking async event persistence interface.
* **Exported Functions:** `persist_event()`, `close_session()`.

---

### 2.5 Analytics & Statistical Engine (`ml/analytics/`)

#### [ml/analytics/service.py](file:///d:/FinalYearProject/ml/analytics/service.py)
* **Lines of Code:** 511 lines | **Role:** Interval analytics, transition matrices, and report generation.
* **Exported Functions:**
  * `process_metric_intervals()`: Executes $G_{\text{max}} = 10.0\text{s}$ gap-filtered timestamp interval duration accounting.
  * `get_summary_analytics()`: Computes total monitored seconds and compliance percentages.
  * `get_posture_analytics()`: Computes observation counts, durations, and posture transition matrices.
  * `get_single_session_detail()`: Downsamples timeline series while preserving critical alert spikes.
  * `get_session_report()`: Synthesizes structured inspection reports.

---

### 2.6 Frontend Client Subsystem (`frontend/src/`)

```text
+------------------------------------+-------+------------------------------------------------------------+
| FILE PATH                          | LINES | PRIMARY FUNCTIONALITY & ARCHITECTURAL ROLE                 |
+------------------------------------+-------+------------------------------------------------------------+
| src/App.jsx                        | 64    | App entry, Context providers, BrowserRouter, ProtectedRoute|
| src/pages/LiveMonitor.jsx          | 425   | Real-time video canvas, target selector, calibration wizard|
| src/pages/Dashboard.jsx            | 421   | Executive KPI cards, Recharts donut, transition heatmap    |
| src/pages/Reports.jsx              | 285   | Session timeline chart, alert audit logs, PDF/JSON export  |
| src/pages/Settings.jsx             | 210   | Voice alert toggles, sensitivity slider, camera selector   |
| src/pages/Login.jsx                | 115   | User login form with client validation and error banners   |
| src/pages/Register.jsx             | 145   | User registration form with matching password checks       |
| src/components/PoseOverlay.jsx     | 380   | 2D Canvas kinematic skeletal joint & bone renderer         |
| src/components/CameraView.jsx      | 240   | HTML5 video element wrapper & canvas frame grabber         |
| src/components/CalibrationCard.jsx | 165   | 10-second interactive countdown wizard card                |
| src/components/AlertBanner.jsx     | 75    | Animated alert toast notification with audio trigger       |
| src/components/TargetSelector.jsx  | 95    | Multi-person candidate selection pill bar                  |
| src/hooks/useMonitoring.js         | 78    | Conductor hook coordinating camera, WebSocket & calibration|
| src/hooks/useCamera.js             | 61    | Hardware getUserMedia stream lifecycle manager             |
| src/hooks/useWebSocket.js          | 110   | Full-duplex WebSocket client with auto-reconnection        |
| src/hooks/useVoiceAlert.js         | 25    | Native Web Speech synthesis text-to-speech engine          |
| src/hooks/useAlertManager.js       | 140   | Active alert queueing and 10-second auto-dismissal timers  |
| src/state/AuthContext.jsx          | 65    | User authentication provider & session verification        |
| src/state/store.js                 | 35    | Global UI state provider & notification toasts             |
| src/utils/postureLabels.js         | 155   | Color tokens, risk configs & 3-state posture synthesizer   |
+------------------------------------+-------+------------------------------------------------------------+
```

---

## 3. Machine Learning Binaries & Evaluation Assets

```text
+------------------------------------------------+----------+---------------------------------------------+
| FILE PATH                                      | SIZE     | ARTIFACT DESCRIPTION                        |
+------------------------------------------------+----------+---------------------------------------------+
| ml/models/selected_development_model.joblib    | 2.65 MB  | Selected Random Forest binary (200 trees)   |
| ml/models/posture_model.joblib                 | 2.65 MB  | Production deployment model binary          |
| ml/models/pose_landmarker_lite.task            | 5.78 MB  | Google MediaPipe BlazePose model asset      |
| reports/ml/model_comparison/model_comparison.json | 3.56 MB| Full 5-fold metric breakdown for all models |
| reports/ml/model_comparison/final_test_evaluation.json | 1.8 KB | Held-out test set performance evaluation   |
| reports/ml/model_comparison/final_test_confusion.png | 22.4 KB | Confusion matrix plot on unseen subjects |
+------------------------------------------------+----------+---------------------------------------------+
```
