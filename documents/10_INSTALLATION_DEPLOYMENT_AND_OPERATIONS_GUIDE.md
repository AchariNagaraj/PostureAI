# PostureAI — Setup, Installation & Deployment Operations Guide

**Document Code:** `DOC-10-OPS`  
**Relative Path:** `documents/10_INSTALLATION_DEPLOYMENT_AND_OPERATIONS_GUIDE.md`  
**Target Environments:** Local Development (Windows / macOS / Linux) & Production Server (Ubuntu / Nginx)  
**Backend Port:** `8000` (FastAPI / Uvicorn)  
**Frontend Port:** `5173` (Vite Dev Server) / `80`/`443` (Nginx Static Serve)  

---

## 1. System Requirements & Prerequisites

Before setting up PostureAI, ensure your host environment meets the following specifications:

```text
+---------------------+---------------------------------------+---------------------------------------+
| COMPONENT           | MINIMUM REQUIREMENT                   | RECOMMENDED PRODUCTION SPECIFICATION  |
+---------------------+---------------------------------------+---------------------------------------+
| Operating System    | Windows 10/11, macOS 12+, Ubuntu 20.04| Ubuntu 22.04 LTS / Debian 12          |
| Python Runtime      | Python 3.10.x                         | Python 3.11.x                         |
| Node.js Runtime     | Node.js v18.x                         | Node.js v20.x (LTS)                   |
| Package Managers    | pip 23+, npm 9+                       | pip, npm, pnpm                        |
| Video Hardware      | Standard 720p 30 FPS USB Webcam       | 1080p 30/60 FPS Integrated or USB Cam |
| CPU / Memory        | Quad-Core CPU, 8 GB RAM               | 8-Core CPU, 16 GB RAM                 |
| GPU Acceleration    | Optional (runs cleanly on CPU)        | NVIDIA CUDA GPU (optional for scale)  |
+---------------------+---------------------------------------+---------------------------------------+
```

---

## 2. Local Development Setup (Step-by-Step)

Follow these sequential steps to establish the complete full-stack environment from source:

### Step 2.1: Clone & Navigate to Repository Root
```bash
cd d:\FinalYearProject
```

### Step 2.2: Set Up Python Virtual Environment
Create and activate an isolated Python virtual environment:
```powershell
# On Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On Linux / macOS (bash):
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2.3: Install Backend Dependencies
Install all required machine learning, vision, database, and ASGI server libraries:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install argon2-cffi itsdangerous pytest
```

Verify that the core packages are correctly recognized:
```bash
python -c "import mediapipe, fastapi, sqlalchemy, sklearn; print('All core Python packages imported successfully!')"
```

### Step 2.4: Configure Environment Variables
Create a `.env` file in the project root based on `.env.example`:
```ini
# Database Connection URL (Defaults to SQLite for local development)
DATABASE_URL=sqlite+aiosqlite:///./postureai.db

# Cryptographic Secret Key for Signing Session Cookies
SECRET_KEY=your_generated_secret_key_here
```

> **MySQL Configuration Note:** To connect to a local or remote MySQL server instead of SQLite, update `DATABASE_URL`:
> ```ini
> DATABASE_URL=mysql+aiomysql://db_user:db_password@localhost:3306/postureai_db
> ```

### Step 2.5: Install Frontend Dependencies
Open a secondary terminal window and set up the React client:
```bash
cd frontend
npm install
```

---

## 3. Launching the Application Locally

To run the complete system locally, launch both the backend server and frontend development server:

### 3.1 Launch FastAPI Backend Server
In Terminal 1 (from repository root with `.venv` active):
```bash
uvicorn ml.api.app:app --host 127.0.0.1 --port 8000 --reload
```
* The API server will start on `http://127.0.0.1:8000`.
* Interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`.
* WebSocket endpoint is active at `ws://127.0.0.1:8000/ws`.

### 3.2 Launch React Frontend Server
In Terminal 2 (inside `frontend/` directory):
```bash
npm run dev
```
* Vite will launch the application on `http://localhost:5173`.
* The frontend automatically proxies API requests (`/api/*`) to `http://127.0.0.1:8000` via `vite.config.ts`.

### 3.3 End-to-End User Verification Workflow
1. Open your browser and navigate to `http://localhost:5173`.
2. Register a new user account at `/register` (e.g., Name: `Demo User`, Email: `demo@postureai.local`).
3. You will be automatically authenticated and redirected to `/live`.
4. Allow browser webcam permissions when prompted by your browser.
5. Sit naturally upright and click **"Start Calibration"**.
6. Hold your comfortable upright posture for the 10-second countdown.
7. Once calibrated, the status indicator will switch to **"GOOD"**, and real-time monitoring begins!

---

## 4. Running the Verification Test Suite

To verify system integrity and run all automated unit and integration tests:

```bash
# Execute full backend test suite
pytest -v ml/tests/ tests/
```

To run frontend component tests:
```bash
cd frontend
npm test
```

---

## 5. Production Deployment Architecture (Ubuntu + Nginx)

For production deployment on an Ubuntu Linux server, configure Nginx as a reverse proxy handling SSL termination and WebSocket upgrades:

```mermaid
graph LR
    User[Client Browser - HTTPS / WSS] --> Nginx[Nginx Reverse Proxy: Port 443]
    Nginx --> |Static Assets: /| DistFolder[/var/www/postureai/dist]
    Nginx --> |API: /api/*| UvicornCluster[FastAPI / Uvicorn Service: Port 8000]
    Nginx --> |WebSocket: /ws| UvicornCluster
    UvicornCluster <--> MySQL[(MySQL Production DB)]
```

### 5.1 Step 1: Build Frontend Production Bundle
```bash
cd frontend
npm run build
# Compiled static assets are output to frontend/dist/
```

### 5.2 Step 2: Systemd Backend Service File
Create `/etc/systemd/system/postureai.service`:
```ini
[Unit]
Description=PostureAI FastAPI WebSocket Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/postureai
EnvironmentFile=/var/www/postureai/.env
ExecStart=/var/www/postureai/.venv/bin/gunicorn ml.api.app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/postureai/access.log \
    --error-logfile /var/log/postureai/error.log

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable postureai
sudo systemctl start postureai
```

### 5.3 Step 3: Nginx Server Block with WebSocket Upgrade
Create `/etc/nginx/sites-available/postureai`:
```nginx
server {
    listen 80;
    server_name postureai.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name postureai.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/postureai.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/postureai.yourdomain.com/privkey.pem;

    root /var/www/postureai/frontend/dist;
    index index.html;

    # Serve React Single Page Application
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy REST API Calls
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy WebSockets with Upgrade Headers
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/postureai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. Operational Troubleshooting Runbook

```text
+------------------------------------+---------------------------------------+------------------------------------+
| SYMPTOM / ERROR                    | ROOT CAUSE                            | REMEDIATION STEP                   |
+------------------------------------+---------------------------------------+------------------------------------+
| Camera Error: "Permission Denied"  | Browser blocked camera access or      | Click camera icon in browser URL   |
|                                    | another app has exclusive lock        | bar; allow permissions; close Zoom.|
+------------------------------------+---------------------------------------+------------------------------------+
| WebSocket Error: "1006 Connection  | FastAPI backend is not running or     | Ensure Uvicorn is active on port   |
| Closed Abnormally"                 | proxy port mismatch                   | 8000; check terminal logs.        |
+------------------------------------+---------------------------------------+------------------------------------+
| "Model file not found" on startup  | Missing .joblib or .task model asset  | Verify ml/models/ contains         |
|                                    | in ml/models/ directory               | selected_development_model.joblib  |
|                                    |                                       | and pose_landmarker_lite.task.     |
+------------------------------------+---------------------------------------+------------------------------------+
| "OperationalError: database locked"| Concurrent writes in SQLite during    | Switch to MySQL in .env or reduce  |
|                                    | rapid development reload              | parallel stress test clients.      |
+------------------------------------+---------------------------------------+------------------------------------+
| No Audio Voice Alert Heard         | System audio muted or browser blocked | Click anywhere on webpage to       |
|                                    | unprompted speech synthesis           | grant audio permission context.    |
+------------------------------------+---------------------------------------+------------------------------------+
| CORS error on /api/auth endpoints  | Frontend not accessing backend via    | Use standard Vite proxy /api or    |
|                                    | configured Vite proxy                 | access via localhost:5173.         |
+------------------------------------+---------------------------------------+------------------------------------+
```
