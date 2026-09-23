# PATHS — Forensic Technical Audit Report

**Audit type:** Read-only forensic audit (no code modified, no dependencies installed)
**Date:** 2026-09-22
**Scope:** Complete repository inspection: source, config, data, models, DB, frontend, Docker, git history
**Executed against:** `D:\1. PROJECTS-MAIN\1. ILA\PATHS`

> Every conclusion below is based on the **actual files** inspected. Where a claim in the README/terminal notes could not be verified in code, it is flagged as a **documentation/implementation discrepancy**.

---

## 0. Inventory: What Was Inspected

### Fully inspected (100% of project code/artifacts)
| Area | Files |
|---|---|
| Backend source | `main.py`, all `api/*` (app, routes, health, auth_routes, decision_routes, analytics_routes, model_routes) |
| ML model | `model/trainer.py`, `model/predictor.py`, `model/paths_model.pkl`, `model/scaler.pkl`, `model_store/v1.pkl`, `model_store/registry.json`, `training/retrain.py` |
| Decision engine | `engine/decision.py`, `engine/paths_logic.py` |
| Data | `data/raw/generate_data.py`, `data/raw/student_data.csv` (500 rows), `data/processed/processed.csv` |
| DB layer | `db/database.py`, `db/models.py`, and both live SQLite files (`paths.db`, `backend/paths.db`) via direct sqlite inspection |
| Auth | `auth/users.py`, `auth/security.py`, `auth/jwt.py`, `core/config.py`, `.env` |
| Frontend | All of `frontend/src/**`, `package.json`, `package-lock.json`, `vite.config.js`, `index.html`, `Dockerfile`, `nginx.conf`, `eslint.config.js` |
| Infra | `docker-compose.yml`, `backend/Dockerfile`, root `.gitattributes`, `requirements.txt` (root + backend), `frontend/package.json` |
| Docs/notes | `README.md` (root + frontend), `terminal.txt`, `counter_run.txt` |
| Git | Full history (9 commits), branches, remote, tracked-file inventory |
| Runtime | `venv` package versions, `.pkl` byte fingerprints, executed model evaluation (read-only) |

### Not inspected (excluded, non-authoritative)
- `venv/` (15,003 files, ~2.8M lines) — Python virtual environment committed into git. It is a frozen install artifact, not project logic.
- `frontend/node_modules/` — standard dependency install, untracked by git.
- `backend/**/__pycache__/` `.pyc` files — compiled artifacts, but note: **they are committed to git** (see §8).

---

## 1. What PATHS Actually Is

**PATHS ("The Coordinate Engine")** is a full-stack web application: a **FastAPI (Python) REST backend + React (Vite) SPA frontend**, whose core is a **hybrid ML + rule-based decision system** that classifies student risk into three categories — **ADVANCE (0), HOLD (1), RETREAT (2)** — and returns an *action*, a *confidence* value, and a *human-readable reason* for a given set of 6 numeric student indicators:

`attendance`, `internal_marks`, `assignments`, `study_hours`, `backlog_count`, `stress_level`

### System classification (with evidence)

| Category | Present? | Evidence |
|---|---|---|
| **Machine learning — trained model** | **YES** | `eval` pipeline in `model/trainer.py:12-25` trains a `sklearn.ensemble.RandomForestClassifier` (200 trees, max_depth 8, class weights `{0:2.5, 1:1.0, 2:1.2}`) and persists it via joblib. Verified independently: loaded `.pkl` is `RandomForestClassifier`, `classes_=[0,1,2]`, `n_features_in_=6`. |
| **ML inference** | **YES** | `model/predictor.py:28-40` scales input then calls `predict_proba`, argmax → class, max probability → "confidence". |
| **Model retraining / versioning** | **YES (partial)** | `training/retrain.py` trains a *different*-config RF (300 trees, max_depth 10, no class weights), writes `model_store/v{n}.pkl`, updates `registry.json`. |
| **Scoring / heuristics / decision rules** | **YES** | `engine/paths_logic.py:1-16` — hard-coded overrides: `attendance < 50 → RETREAT`; `backlogs ≥ 5 AND stress ≥ 8 → RETREAT`; `confidence < 0.6 → HOLD`. |
| **Statistically meaningful dataset** | **Partial** | 500 rows of **synthetic** student data (`data/raw/generate_data.py`), 3 stratified classes with 5% label noise. |
| **Feature engineering** | **None** | Raw 6 features are passed directly; only `StandardScaler` z-scoring (`utils/preprocess.py`). No derived features. |
| **Model evaluation** | **Ad-hoc** | Accuracy + classification report are **printed only**, never persisted or exposed (`trainer.py:22-25`). Verified: test accuracy = **0.99** on the held-out 20%. |
| **Explainability / interpretability** | **Rule text only** | No SHAP/LIME/feature-importance exposure in API. Feature importances exist inside the trained model but are never served. |
| **Confidence scoring** | **Partially** | Confidence = raw max `predict_proba` value (not calibrated). Used only as a threshold gate (≥0.6). |
| **Persistence / database** | **YES** | SQLite via SQLAlchemy, `DecisionLog` table (`db/models.py:4-19`). 2 live DB files exist (see §5). |
| **API** | **YES** | 9 endpoints (see §3). |
| **Frontend/UI** | **YES** | React SPA, 3 screens (Login, Coordinate, Analytics). |

**Verdict: HYBRID system — a RandomForest classification model wrapped by a deterministic rule-override + confidence-threshold decision layer.**
It is a genuine ML-driven system (the model is trained and used for inference), but it is *not* a generic "AI" or LLM system, and the "decision intelligence" is largely produced by 3 explicit hand-coded rules.

---

## 2. Actual Data Flow

```
React SPA (frontend)
   │  axios → http://127.0.0.1:8000   (client.js:3-13, Bearer token interceptor)
   ▼
FastAPI (api/app.py)
   ├─ POST /login      → auth_router       → jwt.create_token         (auth/jwt.py)
   ├─ POST /coordinate → decision_router   → admin_only()  [JWT role check]   (auth/security.py:15)
   │                       │
   │                       ▼
   │              engine/decision.py::coordinate(raw)
   │                       │
   │                       ├─► model/predictor.py::predict(raw)          (scaler.transform → RF.predict_proba → argmax, maxp)
   │                       └─► engine/paths_logic.py::resolve_action(...) (override rules → confidence gate → label map)
   │                       │
   │                       ▼
   │              dict{prediction, action, confidence, reason}
   │                       │
   │                       ▼
   │              SQLAlchemy: DecisionLog.insert(...)   (decision_routes.py:44-59)
   │
   ├─ GET /analytics/*  → analytics_router → SQLite aggregates
   ├─ POST /model/retrain → model_router  → subprocess("python training/retrain.py")  (model_routes.py:10)
   └─ GET /health, /version
```

**Real end-to-end stages that exist:**

```
INPUT (6 numeric fields, Pydantic StudentInput)
  ↓
AUTH GATE (admin-only, JWT Bearer)
  ↓
PREPROCESS (StandardScaler.transform)
  ↓
ML INFERENCE (RandomForest predict_proba → class + confidence)
  ↓
DECISION RULES (2 hard overrides, then confidence<0.6 → HOLD, then label map)
  ↓
RECOMMENDATION (action + reason string)
  ↓
PERSIST (DecisionLog → SQLite)  → RESPONSE (JSON)
  ↓
ANALYTICS (aggregate SQL) — consumed by frontend Analytics page
```

There is **no dedicated validation stage** beyond Pydantic type coercion (`decision_routes.py:12-18`); input ranges are NOT range-checked (see §9, verified DB rows contain out-of-range values).

---

## 3. Architecture Diagram

```mermaid
flowchart TD
    U[Browser / React SPA] -->|POST /login| A
    U -->|POST /coordinate • Bearer JWT| A

    subgraph FastAPI Backend
        A[api/app.py FastAPI + CORS] --> R[api/routes.py]
        R --> H[health.py: GET /health /version]
        R --> AU[auth_routes.py: POST /login]
        R --> D[decision_routes.py: POST /coordinate]
        R --> AN[analytics_routes.py: GET /analytics/summary|confidence|stress-impact]
        R --> M[model_routes.py: POST /model/retrain • GET /model/status]

        D -->|admin_only JWT| SEC[auth/security.py]
        AU --> JWT[auth/jwt.py HS256]
        SEC --> JWT

        D --> E[engine/decision.py :: coordinate]
        E --> P[model/predictor.py :: predict]
        P --> SC[model/scaler.pkl]
        P --> REG[model_store/registry.json → active model .pkl]
        E --> LO[engine/paths_logic.py :: resolve_action]

        D --> DB[(SQLite paths.db :: decision_logs)]
        AN -.-> DB
        M -->|subprocess| RT[training/retrain.py]
        RT --> REG
        RT --> SC
    end

    DB -. startup only .- MAIN[backend/main.py: imports app, no-op]
    DB -. docker mount .- DCOMPOSE[docker-compose backend:/app/paths.db]
```

### Key module map

| Module | Responsibility | Entry |
|---|---|---|
| `backend/api/app.py` | FastAPI app, CORS (allow only `http://localhost:5173`), router wiring | Start: `uvicorn api.app:app` |
| `backend/api/routes.py` | Aggregates 5 sub-routers | — |
| `backend/engine/decision.py` | `coordinate(raw) → {prediction, action, confidence, reason}` | called by `POST /coordinate` |
| `backend/model/predictor.py` | Lazy-loads active model + scaler; inference; confidence | imported by engine |
| `backend/model/paths_model.pkl` | The trained RF (byte-identical to `model_store/v1.pkl`) | loaded via registry |
| `backend/model/scaler.pkl` | StandardScaler persisted at train time | loaded by predictor |
| `backend/model_store/registry.json` | `{active_model: "v1.pkl", history: []}` | read by predictor, written by retrain |
| `backend/engine/paths_logic.py` | Hard-coded overrides + confidence gate + label mapping | imported by engine |
| `backend/db/models.py` | `DecisionLog` table (no timestamp column) | used by coordinate + analytics |
| `backend/api/analytics_routes.py` | 3 aggregate endpoints (admin-only) | — |
| `backend/api/model_routes.py` | Retrain/status (subprocess) | — |
| `backend/auth/*` | Hard-coded users, HTTPBearer, JWT encode/decode | — |
| `frontend/src/**` | React SPA: Login / Coordinate / Analytics | Vite dev or nginx |

### External services / storage
- **No external services.** No LLM, no cloud, no external DB, no message queue.
- **Storage:** local SQLite file(s) via SQLAlchemy 2.0 (`DATABASE_URL = sqlite:///./paths.db`), plus local `.pkl` model artifacts and `registry.json`.

---

## 4. Machine Learning Pipeline (verified, not just documented)

1. **Data generation** — `data/raw/generate_data.py:16-70`
   - 500 rows; 3 generators by class: ADVANCE 28%, HOLD 42%, RETREAT 30%; **5% random label noise** (line 62-64); seed 42.
   - Verified distribution: `risk_level 0→139, 1→209, 2→152`; no nulls.
2. **Split** — `utils/preprocess.py:13-15`: 80/20, `stratify=y`, `random_state=42`.
3. **Scaling** — fit `StandardScaler` **on train only**, persisted to `model/scaler.pkl` (line 17-21).
4. **Model** — `model/trainer.py:12-25`
   - `RandomForestClassifier(n_estimators=200, max_depth=8, class_weight={0:2.5,1:1.0,2:1.2}, random_state=42, n_jobs=-1)`.
5. **Evaluation (re-run read-only by this audit)**: test accuracy **0.99**; per-class f1 ADVANCE 0.98 / HOLD 0.99 / RETREAT 1.00; confusion matrix reveals only 1 misclassification (HOLD→ADVANCE). Mean model confidence 0.957.
6. **Feature importances (from the shipped model)**: attendance 0.250, internal_marks 0.175, study_hours 0.170, stress_level 0.157, backlog_count 0.146, assignments 0.102.
7. **Retraining/versioning** — `training/retrain.py:8-34`
   - **Different hyperparameters from the base trainer** (300 trees, depth 10, **no class weights**) — a configuration mismatch vs `trainer.py`.
   - Writes `model_store/v{len(history)+2}.pkl`, appends to `history`, sets `active_model`. `history` is currently empty ⇒ next retrain yields `v2.pkl`.

> **Caution:** retraining rewrites `model/scaler.pkl` and a **new** `model_store/vN.pkl`, but the in-process model cache (`_model` in `predictor.py:8-20`) only refreshes on **restart**. A retrain via API does not hot-swap the serving model in a running instance — despite "active model dynamically loaded / hot retraining via API" in the README.

**Warning observed during inference verification:** `StandardScaler` was fitted with DataFrame column names, while inference passes a raw numpy array → sklearn emits `X has no valid feature names` warnings (non-fatal).

---

## 5. Storage & Database (verified)

- **Schema** (`db/models.py:4-19`): `decision_logs(id, attendance, internal_marks, assignments, study_hours, backlog_count, stress_level, prediction, action, confidence, reason, triggered_by)`.
- **⚠️ Documentation discrepancy:** README §7 claims logs include a *timestamp*. **There is no timestamp/datetime column** in the table definition or in the actual SQLite schema. Logs cannot be ordered by time. Only `id` order is available.
- **Two databases exist:**
  - `backend/paths.db` — 7 rows (used by Docker mount and runtime from `backend/`).
  - `paths.db` (repo root) — 9 rows (leftover from an older execution where `main.py` was run from repo root). Both are committed to git; `git status` currently shows `backend/paths.db` **modified** (uncommitted).
- **Data-quality finding:** the DB contains rows with values **outside the training ranges**, e.g. `stress_level = 11` (max in data = 9), `study_hours = 8.3` (max ≈ 7.9), and an all-zero row `(0,0,0,0,0,0)` that produced `prediction=HOLD, action=RETREAT, confidence=0.53`. No range validation catches these; the model silently extrapolates.
- Database file `paths.db` (both copies) has identical schema; no other tables.

---

## 6. Decision Engine Truth Table (as implemented in `engine/paths_logic.py`)

Order of checks (first match wins):

| Priority | Condition | Action | Reason string |
|---|---|---|---|
| 1 | `attendance < 50` **OR** (`backlogs ≥ 5` AND `stress ≥ 8`) | RETREAT | "Critical risk detected by rule override" |
| 2 | `confidence < 0.6` | HOLD | "Low confidence in prediction" |
| 3 | prediction == 0 | ADVANCE | "Performance indicators are stable" |
| 4 | prediction == 1 | HOLD | "Moderate risk requires monitoring" |
| 5 | prediction == 2 | RETREAT | "High risk predicted by model" |

Label map (predictor int → name): `0→ADVANCE, 1→HOLD, 2→RETREAT` (`decision.py:4-8`).
Confidence is rounded to 2 decimals in the response.

**Sanity verifications performed (live inference):**
- `[85,78,80,5,0,3] → ADVANCE, 0.995`
- `[45,70,65,3.5,6,9] → model HOLD(0.565), override → RETREAT` (rule resolved correctly)
- `[60,60,60,3,2,5] → HOLD, 0.96`
- `[90,90,90,6,0,2] → ADVANCE, 0.926`
- `[0,0,0,0,0,0] → model HOLD(0.53), override → RETREAT` (matches DB row 5)

---

## 7. Authentication (verified)

- **Scheme:** `HTTPBearer` + JWT (HS256) via `python-jose` — `auth/security.py:5-18`.
- **Roles:** only two users, **hard-coded in plaintext** in `backend/auth/users.py`:
  - `admin@paths.io / admin123` → admin
  - `viewer@paths.io / viewer123` → viewer
- **Login compares the raw password string** (`auth_routes.py:15`) — no hashing. Note `passlib[bcrypt]` **is installed** in the venv but is never imported/used.
- **Secret handling:** `JWT_SECRET=paths_secret_key` lives in `backend/.env` **which is committed to the repo**. Default fallbacks in `core/config.py` mean the app also works without `.env`.
- `admin_only` denies non-admin with 403; `/coordinate`, `/analytics/*`, `/model/*` are admin-gated. `/health`, `/version`, `/login` are public.

---

## 8. Repository & Git Hygiene (verified)

- **9 commits** (all 2025-12-19/21, single working branch `main`, remote `origin → github.com/ilangovan11/PATHS.git`):
  1. `e88538b` Initial commit
  2. `ac2c206` ML model trained
  3. `4d69697` backend integrated
  4. `632d34e` Authorizations
  5. `0231575` database integrated
  6. `0d76d12` Analytics admin
  7. `efa1089` Frontend connected
  8. `c76da82` Retraining & Versioning
  9. `777862e` Docker integration
- **⚠️ Repo hygiene problems (verified):**
  - **`venv/` is committed** — 15,003 of 15,089 tracked files (~99.5% of the repo) are the Python virtual environment.
  - `backend/**/__pycache__/*.pyc` committed.
  - Binary artifacts committed: `model/*.pkl`, `model_store/v1.pkl`, `paths.db`, `backend/paths.db`.
  - **No root `.gitignore`** exists (only `frontend/.gitignore`).
  - `backend/.env` committed (contains hard-coded secret).
- **No tests** of any kind in the project (no `test/`, `tests/`, `pytest.ini`, `conftest.py`). The only test files found live inside `venv/` (third-party package tests) — NOT project tests.
- No CI configuration, no `pyproject.toml`/`setup.py`, no lint/typecheck config for the backend.

---

## 9. Dead Code, Dead Artifacts & Documentation Gaps (verified)

| Item | Status |
|---|---|
| `backend/main.py` | Effectively dead — the entire body (DB create + uvicorn run) is **commented out** (lines 2-9). Entry point in practice is `uvicorn api.app:app`. |
| `backend/utils/metrics.py` | **Empty file (0 bytes).** |
| `backend/data/processed/processed.csv` | **Empty file (0 bytes).** Nothing in the pipeline ever writes it; data goes CSV → scaler arrays directly. |
| `backend/db/__init__.py` | **Missing** — `db` works only as a PEP-420 namespace package. |
| `fastapi-security`, `passlib[bcrypt]`, `python-jose`* | Installed; only `python-jose` is used. `fastapi-security` and `passlib` are unused. (`*jose` is used via `auth/jwt.py`.) |
| `frontend` `react-router-dom` dependency | Declared in `package.json` but **never imported** — navigation is manual `useState` toggling in `App.jsx`. |
| README claims | "Timestamped logs" (no timestamp column), "hot retraining / active model dynamically loaded" (no hot-swap of in-memory cache), "model registry retained history" (history empty) — all **partially or fully inaccurate** vs the code. |
| `counter_run.txt` | Documents a manual workaround (`copy model\paths_model.pkl model_store\v1.pkl`) — a sign that the initial registry sync was a manual step, not automated. |

---

## 10. Frontend (verified)

- **Stack:** React 19, Vite 7, axios. Plain JavaScript (`.jsx`), no TypeScript.
- **App shell** (`App.jsx`): login-gate via `AuthContext` token state; 3 nav buttons; page state switching.
- **`AuthContext.jsx`:** stores JWT in `localStorage`.
- **`api/client.js`:** axios instance, **baseURL hard-coded `http://127.0.0.1:8000`**; request interceptor attaches Bearer token.
- **`Login.jsx`:** calls `POST /login`, error from response detail.
- **`Coordinate.jsx`:** 6 numeric inputs → `POST /coordinate`; renders action/confidence/reason.
- **`Analytics.jsx`:** fetch only `/analytics/summary`. Note: `/analytics/confidence` and `/analytics/stress-impact` exist server-side but are **not consumed** by the UI.
- Note: `node_modules` present and git-ignored; `dist` not present (never built locally).

---

## 11. Containerization (verified)

- `docker-compose.yml`: backend build `./backend`, port `8000:8000`, env_file `./backend/.env`, volume mounts `./backend/paths.db:/app/paths.db`; frontend build `./frontend`, port `5173:80`, depends_on backend.
- `backend/Dockerfile`: `python:3.10-slim`, `pip install -r requirements.txt`, `COPY . .`, `CMD uvicorn api.app:app --host 0.0.0.0 --port 8000`.
- `frontend/Dockerfile`: Node 20 build stage → nginx serve with `nginx.conf` SPA fallback.
- **Latent Docker bug (design-level):** with Nginx frontend on port `80` mapped to `5173`, the browser origin is `http://localhost:5173` so CORS passes; but the API `baseURL` is hard-coded to `127.0.0.1:8000`, so accessing the UI from any non-localhost host, or the future deployment, breaks both CORS and the base URL. Nginx has **no `/api` reverse proxy to the backend**.

---

## 12. Definitive Findings Summary

1. **PATHS is a real ML-based decision-support web app** — hybrid RF-classifier + hand-coded override rules. Not rule-only, not LLM-based.
2. **The trained model is real and functional**: verified 0.99 accuracy on synthetic holdout; inference works.
3. **The rules layer is small and brittle** (2 hard thresholds + 1 confidence gate) and silently extrapolates on out-of-range input because there is **no input range validation**.
4. **No tests, no CI, no evaluation persistence** — the "production-ready ML system" claim in the README is not supported by the repository.
5. **Secrets & repo hygiene issues**: committed `.env` with JWT secret, plaintext hard-coded credentials, `venv/` + `__pycache__` + binary artifacts committed, no root `.gitignore`.
6. **Significant documentation/implementation gaps**: no log timestamp (README says there is), no hot model swap, empty `history`, dead files (`metrics.py`, `processed.csv`), commented-out `main.py`, unused deps (passlib, fastapi-security, react-router-dom).
7. **Two divergent DB files** (root vs `backend/`) — schema identical, no timestamp — and `backend/paths.db` currently dirty in git.
8. **Retrain path has an internal config mismatch** (300trees/depth10/no class-weights vs 200trees/depth8/weights) and does **not** update the in-memory serving model.
9. **Docker setup lacks an API proxy** and relies on hard-coded localhost — fine for local dev only.

### Not counted as ML (contrary to what marketing wording might imply)
- **"Decision intelligence"** = 3 hard-coded `if` conditions.
- **Confidence** = uncalibrated max softmax-probability, used as a single threshold.
- **"Explainability"** = a static reason string; no feature/contribution attribution exposed.
- **No deep learning, no LLM, no neural network, no Bayesian/statistical modeling beyond RandomForest.**

---

*End of audit — authoritative baseline. No files were modified; the only write produced by this session is this report (`report.md`).*

---

# PART 2 — Upgrade Outcome (AFTER)

**Date:** 2026-09-22 (same repo, same session's follow-up project)
**Method:** verified, phased upgrade. Every claim below was produced by an executed check (tests, smoke, builds, containers). Full per-phase record: `UPGRADE_PROGRESS.md`; final matrix: `FINAL_AUDIT.md`.

## 13. What Changed (vs the §1–§12 baseline)

| Baseline (§) | BEFORE | AFTER (verified) |
|---|---|---|
| §4 training config mismatch | retrain used 300 trees / depth 10 / no weights ≠ serving 200/8/weights | single `MODEL_CONFIG` in `model/config.py`; retrain == serve |
| §4 hot-swap | in-memory cache only refreshed on restart | registry/version watch + `flush()`; hot reload E2E-tested |
| §4 scaler warning | `X has no valid feature names` on inference | feature-order-guarded; inference clean |
| §5 schema | no timestamp; no model version; no trace; no `users` table | `created_at`, `model_version`, `decision_trace` (`DecisionLog`), `User` table; **additive, idempotent migration**; prior 7 rows preserved (DB now has 10) |
| §5 data quality | out-of-range inputs silently extrapolated | Pydantic range validation → **422**; no new out-of-range writes |
| §6 rules | semantics identical (override → gate → map) | preserved verbatim; now exposed as `rules_checked` |
| §7 auth | plaintext passwords; `passlib` unused; committed `.env` secret | bcrypt hashes; `passlib` dropped; secret default = ephemeral `secrets.token_hex(32)` when unset/`change-me`; no committed secret |
| §7 scope | `/coordinate`, `/analytics/*`, `/model/*` all admin-only | viewer = read-only analyst (analytics + model read OK); write/modify admin-only |
| §8 hygiene | `venv/`, `__pycache__`, `.pkl`, `.db`, `.env` committed; no root `.gitignore`; 9 commits | untracked via root `.gitignore`; `.env.example` added; stale binary artifacts `git rm`-ed (uncommitted, as policy) |
| §9 dead code | `metrics.py` 0 bytes, `processed.csv` 0 bytes, commented `main.py`, unused `react-router-dom`, unused deps | metrics real & persisted; `main.py` is the honest runner; router SPA; deps cleaned |
| §9 docs gaps | "timestamped logs", "hot retraining", "retained history" claims inaccurate | claims now implemented; docs rewritten to match reality |
| §10 frontend | hard-coded `127.0.0.1:8000`; manual page switching; partial analytics | `VITE_API_BASE_URL`/`/api`; React Router + protected routes; all analytics + model pages wired; charts custom CSS |
| §11 Docker | no `/api` proxy; frontend on 5173; file-mount DB | nginx `/api` proxy verified; frontend on 8080; named-volume DB; build+run+teardown all verified |

## 14. New Verification Results (all executed)

- Backend automated tests: **47 passed** (25.49 s).
- Model v1 (new store): accuracy **0.99**, f1_macro **0.9901**, eval n=100; registry `active_model=v1`; feature importances persisted and served.
- Live smoke (localhost:8000, admin+viewer): health `alive/db=ok/v1`; login both roles; 401 (no token) / 403 (viewer coordinate); coordinate healthy→ADVANCE 0.9991 / critical→RETREAT override / invalid→422; analytics real aggregates (10 = 3/4/3); model status+versions populated; retrain/activate admin-only.
- Frontend: lint 0/0; production build PASS (299.66 kB JS / 11.14 kB CSS); Vite `/api` dev proxy verified live.
- Docker (`docker compose`): build PASS; backend `db=ok model=v1`; SPA 200 @ :8080 with PATHS title; `/api/health`, `/api/version`, `/api/login` through nginx PASS; `down` clean.
- Demo scenarios captured live in `DEMO_SCENARIOS.md`.

## 15. Residual Limitations (honestly stated)

- Synthetic 500-row dataset; 0.99 accuracy is on the synthetic holdout, not real-world evidence.
- Confidence = max `predict_proba`, uncalibrated; 0.6 gate is a heuristic.
- Rules live in code; SQLite single-writer; no CI, no rate limiting, no app-level TLS.
- Long-lived deployments MUST set a strong `JWT_SECRET` (default is ephemeral-by-design for dev).
- Root `paths.db` (legacy layout) and `backend/.env` remain on disk only as untracked local residue.

*End of Part 2. Baseline (§1–§12) intentionally unchanged for forensic comparison.*