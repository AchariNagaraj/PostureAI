# PostureAI

![GitHub Repo Size](https://img.shields.io/github/repo-size/AchariNagaraj/PostureAI)
![GitHub License](https://img.shields.io/github/license/AchariNagaraj/PostureAI)
![GitHub Stars](https://img.shields.io/github/stars/AchariNagaraj/PostureAI?style=social)

---

## 📖 Project Overview
**PostureAI** is an end‑to‑end, privacy‑preserving, real‑time computer‑vision and machine‑learning system that monitors sitting ergonomics using a standard 2‑D webcam. It extracts 3‑D skeletal landmarks, engineers eight biomechanical features, classifies posture into five classes, and runs a temporal risk engine that alerts only on sustained bad posture.

The repository contains a **full‑stack application**:
- **Frontend** – React 18 + Vite + Tailwind CSS UI with live webcam overlay and dashboards.
- **Backend** – FastAPI 0.115 + Uvicorn, asynchronous SQLAlchemy 2.0, WebSocket streaming for real‑time telemetry.
- **ML / CV** – MediaPipe PoseLandmarker Lite, Random‑Forest classifier (`posture_model.joblib`).
- **DevOps** – Scripts for training, model comparison, and deployment guides.

> All documentation lives in the `documents/` folder. See the **Master Index** for a navigation matrix.

---

## 📚 Table of Contents
- [Features](#-features)
- [Architecture Overview](#-architecture-overview)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [Model Files](#-model-files)
- [Project Documentation](#-project-documentation)
- [Development Workflow](#-development-workflow)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features
- **Real‑time posture classification** (5 classes) with > 97 % test accuracy on unseen subjects.
- **Unified viewpoint‑robust model** – a single classifier works for front & side views.
- **Zero‑switching multi‑person tracker** – never silently changes the target.
- **Personal calibration wizard** – subject‑independent baseline normalization.
- **Temporal risk state machine** – persistence, cooldown, and recovery logic to avoid alert fatigue.
- **Full‑stack UI** – live webcam overlay, dashboards, analytics, and settings.
- **Comprehensive test suite** – unit, integration, and performance tests.
- **Docker‑ready deployment** – guides for local dev and production.

---

## 🏗️ Architecture Overview
High‑level system design is described in **[02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md](file:///d:/FinalYearProject/documents/02_SYSTEM_ARCHITECTURE_AND_DATAFLOW.md)**.

- **Frontend** (`frontend/`) – React components, custom hooks (`useMonitoring`, `useWebSocket`, `useAlertManager`), and Tailwind‑styled UI.
- **Backend API** (`ml/api/`) – FastAPI routers, WebSocket endpoint (`/ws`), authentication (Argon2), and SQLAlchemy models.
- **ML / CV Pipeline** (`ml/inference/` & `ml/models/`) – MediaPipe pose extraction → feature vector → Random‑Forest inference → temporal risk engine.
- **Persistence** – SQLite (dev) / MySQL‑compatible (prod) with Alembic migrations.

---

## ⚙️ Installation & Setup
1. **Clone the repo** (already done) and navigate to the project root.
2. **Create a virtual environment** and install Python dependencies:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Install frontend dependencies**:
   ```powershell
   cd frontend
   npm install
   ```
4. **Configure environment variables** – copy `.env.example` to `.env` and fill in the required values (DB URL, secret keys, etc.).
5. **Run database migrations**:
   ```powershell
   alembic upgrade head
   ```
6. **Verify model files** – `ml/models/` must contain `posture_model.joblib` and `selected_development_model.joblib` (see [Model Files](#-model-files)).

---

## 🚀 Running the Application
- **Backend** (development):
  ```powershell
  uvicorn ml.api.app:app --reload
  ```
- **Frontend** (development):
  ```powershell
  cd frontend
  npm run dev   # already running in your session
  ```
- Open `http://localhost:5173` in a browser. The UI will connect to the backend via WebSocket and start streaming webcam frames.

---

## 📦 Model Files
| Model file | Relative path | Size | Purpose |
|------------|---------------|------|---------|
| `posture_model.joblib` | `ml/models/posture_model.joblib` | ~2.65 MB | Production Random‑Forest classifier used by the inference service. |
| `selected_development_model.joblib` | `ml/models/selected_development_model.joblib` | ~2.65 MB | Development/experimental Random‑Forest classifier used for experiments and model‑selection. |
| `viewpoint_robust_model.joblib` | `ml/models/viewpoint_robust_model.joblib` | (small) | Adds viewpoint‑robustness to the pipeline (referenced in the master context). |

---

## 📚 Project Documentation
All detailed documentation is stored in the **`documents/`** folder. Key files:
- **[00_EXECUTIVE_SUMMARY_AND_MASTER_INDEX.md](file:///d:/FinalYearProject/documents/00_EXECUTIVE_SUMMARY_AND_MASTER_INDEX.md)** – high‑level summary and navigation matrix.
- **[01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md](file:///d:/FinalYearProject/documents/01_PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md)** – motivation and scope.
- **[04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md](file:///d:/FinalYearProject/documents/04_MACHINE_LEARNING_PIPELINE_AND_EXPERIMENTS.md)** – training, validation, and model comparison.
- **[08_FRONTEND_ARCHITECTURE_AND_UI_UX.md](file:///d:/FinalYearProject/documents/08_FRONTEND_ARCHITECTURE_AND_UI_UX.md)** – React component tree and UI flows.
- **[10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md](file:///d:/FinalYearProject/documents/10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md)** – step‑by‑step setup and troubleshooting.
- **[12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md](file:///d:/FinalYearProject/documents/12_COMPLETE_SOURCE_CODE_CATALOG_AND_FILE_DIRECTORY.md)** – exhaustive source‑code listing.

---

## 🛠️ Development Workflow
1. **Make changes** in the appropriate module (`ml/`, `frontend/`, or `scripts/`).
2. **Run tests** to ensure nothing breaks:
   ```powershell
   pytest
   ```
3. **Commit** with conventional commits (e.g., `feat: add X`, `fix: correct Y`).
4. **Push** to the remote `dev` branch (already set up).
5. Open a Pull Request on GitHub for code review.

---

## 🤝 Contributing
Contributions are welcome! Please:
- Fork the repository.
- Create a feature branch (`git checkout -b feat/awesome-feature`).
- Follow the existing coding style and run the test suite.
- Submit a Pull Request with a clear description.

See the **[CONTRIBUTING.md]** (to be added) for detailed guidelines.

---

## 📄 License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

*Built with ❤️ for ergonomics research and real‑time AI.*
