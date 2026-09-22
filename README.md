# PATHS — The Coordinate Engine

**PATHS** is a cloud-ready full‑stack **student risk decision‑support application**: a FastAPI (Python 3.10) backend, a React (Vite) SPA dashboard, and a hybrid **RandomForest classifier + deterministic safety-rule** decision engine. For a student profile of 6 numeric indicators it returns an **interpretable action** — **ADVANCE**, **HOLD**, or **RETREAT** — together with model confidence, per-class probabilities, feature importances, and a 5-step decision trace.

> **Honest description (verified):** the ML part is a real, trained `RandomForestClassifier`; the "decision intelligence" layer is 3 explicit rules (2 critical-risk overrides + a confidence gate). Confidence is the raw max class probability — **model confidence, not calibrated**. Training data is **synthetic** (500 rows, 5% label noise). This is a demo/sandbox system, not a validated production ML service.

---

## 1. System Overview

**Input features**

| Feature | Range enforced by the API |
|---|---|
| `attendance` | 0 – 100 |
| `internal_marks` | 0 – 100 |
| `assignments` | 0 – 100 |
| `study_hours` | 0 – 16 |
| `backlog_count` | 0 – 20 |
| `stress_level` | 1 – 10 |

The API rejects out-of-range values with HTTP 422.

**Decision layer (order of checks, first match wins)**

| Priority | Condition | Action |
|---|---|---|
| 1 | `attendance < 50` **or** (`backlog_count ≥ 5` **and** `stress_level ≥ 8`) | **RETREAT** — "Critical risk detected by rule override" |
| 2 | model confidence < 0.6 | **HOLD** — "Low confidence in prediction" |
| 3 | model class 0 | **ADVANCE** — "Performance indicators are stable" |
| 4 | model class 1 | **HOLD** — "Moderate risk requires monitoring" |
| 5 | model class 2 | **RETREAT** — "High risk predicted by model" |

## 2. Architecture

```
Browser (SPA, React Router)
   │ axios baseURL = VITE_API_BASE_URL  (dev: /api via Vite proxy → backend; prod: nginx /api proxy)
   ▼
FastAPI backends
   ├─ POST /login            → JWT (HS256)
   ├─ GET  /analytics/*      → summary, confidence stats, stress-impact, recent (authenticated)
   ├─ POST /coordinate       → decision engine service call + persist (admin)
   ├─ GET  /model/status|versions → registry/metadata/metrics (authenticated)
   ├─ POST /model/retrain    → train new version + promotion check (admin)
   ├─ POST /model/activate   → flip active version (admin)
   └─ GET  /health | /version
```

- **Engine**: `engine/decision.py` orchestrates `model/predictor.py` (hot-reloading inference) + `engine/paths_logic.py` (rules).
- **Model store**: `model_store/<vN>/{model.pkl, scaler.pkl, metrics.json, metadata.json}` + `model_store/registry.json` driving the active version.
- **Persistence**: SQLite via SQLAlchemy (`decision_logs`, `users`).
- **Security**: `bcrypt` password hashes, `python-jose` JWT, role-based access (viewer = read-only analyst).

## 3. Project Structure

```
.
├── backend/
│   ├── api/            # FastAPI routers (app, routes, health, auth, decision, analytics, model)
│   ├── auth/           # jwt, security, users (bcrypt)
│   ├── core/           # config, logging, validation
│   ├── db/             # database, models, migration
│   ├── engine/         # decision.py, paths_logic.py (rules)
│   ├── model/          # trainer.py, predictor.py, registry.py, config.py (shared config)
│   ├── model_store/    # versioned artifacts + registry.json   (git-tracked, v1)
│   ├── training/       # retrain.py (run_retrain, activate)
│   ├── utils/          # preprocess.py, metrics.py
│   ├── tests/          # pytest suites (47 tests)
│   ├── data/raw/       # student_data.csv + generate_data.py (synthetic)
│   ├── requirements.txt / requirements-dev.txt
│   └── Dockerfile  /  .dockerignore
├── frontend/           # React + Vite SPA (vite.config, nginx.conf, Dockerfile)
├── data/               # data generation source (older layout reference)
├── docker-compose.yml
├── .env.example
└── README.md
```

Note: the operational SQLite DB lives at `backend/paths.db` (git-ignored). Older/inactive layouts (`model/`, `training/` at top level as symlinks of the past, root `paths.db`) are historical and untracked.

## 4. Authentication & Roles

Demo accounts (seeded on a fresh database, bcrypt-hashed; overridable via `ADMIN_PASSWORD` / `VIEWER_PASSWORD`):

| User | Password | Role |
|---|---|---|
| `admin@paths.io` | `admin123` | admin |
| `viewer@paths.io` | `viewer123` | viewer |

| Route group | admin | viewer |
|---|---|---|
| `/coordinate`, `/model/retrain`, `/model/activate` | ✅ | ❌ 403 |
| `/analytics/*`, `/model/status`, `/model/versions` | ✅ | ✅ |

Tokens are JWT (HS256), default 60 min expiry. **Do not use the demo credentials or the default secret in real deployments.**

## 5. Configuration

Copy `.env.example` to `.env` at the repo root (backend reads the **root** `.env`):

```
APP_NAME=PATHS
APP_VERSION=2.0.0
ENV=development

JWT_SECRET=             # leave empty/show "change-me" for an ephemeral dev secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Optional path/credential overrides
DATABASE_URL=
MODEL_STORE_DIR=
ADMIN_EMAIL=
ADMIN_PASSWORD=
VIEWER_EMAIL=
VIEWER_PASSWORD=
```

Security note: if `JWT_SECRET` is empty or literally `change-me`, a random ephemeral secret is generated at startup — the app always runs locally without a committed secret, but issued tokens do not survive a restart. Set a strong `JWT_SECRET` for any long-lived instance.

## 6. Running Locally

**Backend**

```powershell
# from the repo root, using the project venv
venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt            # + backend\requirements-dev.txt for tests
python backend\model\trainer.py                    # trains v1 in backend\model_store (idempotent)
python -m uvicorn api.app:app --app-dir backend --port 8000
```

**Frontend (dev)**

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173  — proxies /api → http://127.0.0.1:8000
```

**Tests**

```powershell
python -m pytest backend\tests -q        # 47 passed
```

## 7. Running with Docker (single command)

```powershell
docker compose up --build
```

- Backend: `http://localhost:8000` (health at `/health`).
- Frontend: `http://localhost:8080` (Nginx serves the SPA and reverse-proxies `/api` → backend).
- A named volume (`paths_data`) persists the SQLite DB across container restarts.
- Set `JWT_SECRET` from your environment for a non-ephemeral secret: `$env:JWT_SECRET="..."`.

## 8. API Reference (summary)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | liveness: status, environment, db, active_model |
| GET | `/version` | none | app name + version (2.0.0) |
| POST | `/login` | none | `{email, password}` → `{access_token, role, email}` |
| GET | `/auth/me` | bearer | current user |
| POST | `/coordinate` | admin | evaluate a profile, persist, return decision + trace |
| GET | `/analytics/summary` | any user | decision counts |
| GET | `/analytics/confidence` | any user | avg/min/max confidence |
| GET | `/analytics/stress-impact` | any user | stress × action distribution |
| GET | `/analytics/recent?limit=` | any user | recent logged decisions |
| GET | `/model/status` | any user | active model, metrics, metadata |
| GET | `/model/versions` | any user | registry history |
| POST | `/model/retrain` | admin | train new version + promotion policy |
| POST | `/model/activate` | admin | `{version}` switch active model |

`POST /coordinate` body and (abridged) response:

```json
{
  "attendance": 90, "internal_marks": 85, "assignments": 88,
  "study_hours": 6, "backlog_count": 0, "stress_level": 3
}
```
```json
{
  "prediction": "ADVANCE",
  "action": "ADVANCE",
  "confidence": 0.9991,
  "reason": "Performance indicators are stable",
  "model_version": "v1",
  "probabilities": { "0": 0.9991, "1": 0.0009, "2": 0.0 },
  "rules_checked": [
    { "rule": "critical_risk_override", "condition": "attendance < 50 OR (backlogs >= 5 AND stress >= 8)", "triggered": false },
    { "rule": "low_confidence_gate", "condition": "confidence < 0.6", "triggered": false },
    { "rule": "model_prediction_map", "condition": "model prediction is ADVANCE", "triggered": true }
  ],
  "trace": [
    "Input validated against documented feature ranges.",
    "Features scaled using the active model's StandardScaler (model v1).",
    "Model prediction: ADVANCE (confidence 0.999).",
    "Safety rules evaluated.",
    "Final action: ADVANCE."
  ],
  "feature_importances": [
    { "feature": "attendance", "importance": 0.2501 },
    { "feature": "internal_marks", "importance": 0.1756 },
    { "feature": "assignments", "importance": 0.1017 },
    { "feature": "study_hours", "importance": 0.1699 },
    { "feature": "backlog_count", "importance": 0.146 },
    { "feature": "stress_level", "importance": 0.1567 }
  ]
}
```

## 9. Dashboard Pages

- **Login** — email + password → JWT; role-aware.
- **Dashboard** — model vitals, recent decisions, action mix.
- **Coordinate** — enter a student profile, review the decision, probabilities, and full trace.
- **Analytics** — decision counts, confidence stats, stress vs action, recent log.
- **Model Insights** — active model metrics and per-feature importance (custom charts).
- **Model Management** — (admin) retrain and activate versions from the registry.

## 10. Design Decisions & Limitations (honest)

- Synthetic 500-row dataset; accuracy ~0.99 on the synthetic holdout is **not evidence of real-world performance**.
- Confidence is uncalibrated `max(predict_proba)`; the 0.6 gate is a heuristic, not a calibrated threshold.
- Rules live in code (`engine/paths_logic.py`) — changing them requires a code change + tests.
- SQLite is single-writer and file-based; suited to light deployments only.
- No CI pipeline, no TypeScript, no API authentication rate-limiting (tokens expire, but no throttling).
- Retraining promotes only when `f1_candidate ≥ f1_active − 0.01`; otherwise the candidate is stored as inactive.

## 11. Documentation Index

- `baseline_report.md` — pre-upgrade forensic audit (authoritative baseline).
- `UPGRADE_PLAN.md` — planned phases.
- `UPGRADE_PROGRESS.md` — phase-by-phase results with evidence.
- `FINAL_AUDIT.md` — post-upgrade verification matrix.
- `DEMO_SCENARIOS.md` — live runnable scenarios with recorded outputs.
- `report.md` — audit + upgrade outcome (BEFORE → AFTER).