# PATHS 2.0 — Upgrade Progress Report

**Project:** PATHS (The Coordinate Engine) — FastAPI + React + RandomForest hybrid risk-decision system
**Repository:** `D:\1. PROJECTS-MAIN\1. ILA\PATHS`
**Date:** 2026-09-22
**Process:** Verifiable, phased upgrade. Every claim in this document is backed by an executed check; statuses are only `PASS`, `FAIL`, `BLOCKED`, `NOT VERIFIED`, or `SKIPPED`. No git commits were created, no history rewritten.

---

## Phase 0 — Baseline & Plan

| Activity | Status | Evidence |
|---|---|---|
| Read-only forensic audit of the entire repo (9 commits, all source, models, DBs, Docker, frontend) | PASS | `baseline_report.md` (authoritative audit baseline) |
| Upgrade plan produced | PASS | `UPGRADE_PLAN.md` |

Baseline defects found (verified): no tests; committed `venv/`, `__pycache__`, `.env` with a secret, binary `.pkl`/`.db` artifacts; no root `.gitignore`; plaintext passwords + `passlib` installed but unused; no input range validation (out-of-range rows present in DB); no log timestamp; metrics never persisted/exposed; `/coordinate` responses not machine-readable; frontend with hard-coded `127.0.0.1:8000` API URL, no `/api` proxy in Nginx, manual page-switching; `react-router-dom` installed but unused; no Docker `/api` proxy; retrain path with a hyperparameter mismatch and no hot-swap; dead files (`utils/metrics.py` 0 bytes, `processed.csv` 0 bytes, commented-out `main.py`); stale `counter_run.txt` / `terminal.txt` workaround notes.

## Phase 1 — Repository Hygiene & Security

| Activity | Status | Evidence |
|---|---|---|
| Root `.gitignore` created (venv, `*.db`, `.env`, `__pycache__`, `node_modules`, build output) | PASS | `git status` clean of these afterwards |
| `.env.example` created at root; no real secret in repo | PASS | file inspected |
| Stop tracking virtualenv, DBs, `.env`, `__pycache__` (`git rm --cached`) | PASS | `git status` — items now untracked; working tree intentionally uncommitted |
| Remove stale `backend/.env.example` | PASS | file removed (tracked removal not committed) |
| `backend/.env` (unused by new loader, untracked) left on disk as developer-only local file | PASS | documented decision |

## Phase 2 — Backend Foundation (config / logging / validation / DB)

| Activity | Status | Evidence |
|---|---|---|
| `core/config.py` rebuilt — single root `.env` loader; `JWT_SECRET=change-me` treated as unset → ephemeral `secrets.token_hex(32)`; validated env defaults | PASS | `backend/core/config.py` inspected; smoke tests ran with no `.env` |
| `core/logging.py` structured file + console logger | PASS | file inspected; logs emitted during smoke/Docker runs |
| `core/validation.py` — documented feature ranges | PASS | ranges: attendance 0–100, internal_marks 0–100, assignments 0–100, study_hours 0–16, backlog_count 0–20, stress_level 1–10 |
| `db/database.py` + `db/models.py` + `db/migration.py` — additive idempotent schema upgrade (adds `created_at`, `model_version`, `decision_trace`, `User` table), auto applied at startup | PASS | `ensure_schema` runs in `api/app.py` lifespan; DB migrated in place with existing rows preserved |
| Arguments `KeyError`/`IndexError` free across new modules | PASS | all runtime paths exercised in smoke/dev/Docker runs |

## Phase 3 — Authentication & RBAC

| Activity | Status | Evidence |
|---|---|---|
| Plaintext passwords replaced with `bcrypt` hashes (direct `bcrypt`; `passlib` removed) | PASS | `auth/security.py`, `auth/users.py`; DB `users` table holds bcrypt digests |
| Seeded demo accounts on fresh DB: `admin@paths.io` / `admin123`, `viewer@paths.io` / `viewer123` (env-overridable, honoring JWT secret fallback) | PASS | login smoke tests for both roles |
| JWT via `python-jose` HS256 with configurable expiry | PASS | `auth/jwt.py`; login smoke test |
| Role policy corrected: **viewer = read-only analyst** — `/analytics/*`, `/model/status`, `/model/versions` allowed; `/coordinate`, `/model/retrain`, `/model/activate` admin-only | PASS | tests + smoke: no-token → 401, viewer on coordinate → 403, viewer on analytics/model reads → 200 |
| Deprecated path role logic removed | PASS | audit trail in git diff (working tree) |

## Phase 4 — Input Validation

| Activity | Status | Evidence |
|---|---|---|
| Pydantic bounds on all 6 features at the API boundary | PASS | `api/decision_routes.py` `StudentInput` |
| Invalid inputs return 422 with clear details | PASS | smoke test: 422; parametrized unit tests |
| Out-of-range extrapolation defect closed | PASS | unit tests `test_validation.py` (10 parametrized invalid cases) |

## Phase 5 — ML Pipeline Hardening

| Activity | Status | Evidence |
|---|---|---|
| Single training pipeline (`model.trainer.train`) — data gen, split, scale, train, persist, metrics, registry write | PASS | `backend/model/trainer.py` |
| `StandardScaler` names-warning defect fixed (feature-name-safe transform, no sklearn warnings) | PASS | predictor inference runs clean; feature-order guard via `FEATURE_ORDER` |
| Metrics persisted + exposed (`metrics.json`, `metadata.json` per version) | PASS | `model_store/v1/metrics.json`; `/model/status` returns real metrics |
| Feature importances served | PASS | `/model/status` + `/coordinate` response |
| Versioned store `model_store/<vN>/{model.pkl, scaler.pkl, metrics.json, metadata.json}` + `registry.json` with `history` | PASS | `registry.json` now populated; `/model/versions` |
| Promotion policy: candidate promoted if `f1 >= active_f1 - 0.01` else registered inactive | PASS | `model/config.py` `PROMOTION_TOLERANCE`; retrain path + unit tests |
| Hot reload of serving model (registry mtime/active-version watch, thread-safe) | PASS | `model/predictor.py`; tested via `service.pump()`/`flush()` + retrain E2E |
| Retrain config matches serving config (single source of truth in `model/config.py`) | PASS | retrain uses same `MODEL_CONFIG` as trainer |
| **v1 retrained in the new store** — active model `v1` | PASS | accuracy **0.99**, f1_macro **0.9901**, 6 features; `active_model=v1` |
| Old artifacts removed from tracking (`model/paths_model.pkl`, `model/scaler.pkl`, `model_store/v1.pkl`) | PASS | `git rm` (uncommitted); docs still reference old paths in `baseline_report.md` only |

## Phase 6 — Decision Engine & API

| Activity | Status | Evidence |
|---|---|---|
| Rule semantics preserved verbatim from baseline (2 hard overrides → confidence gate → label map) | PASS | unit tests `test_rules.py`; smoke scenarios |
| `/coordinate` response extended with `model_version`, `probabilities`, `feature_importances`, `rules_checked`, `trace` (details in `decision.py`), while keeping legacy fields | PASS | `retrograde`: legacy field set is a true subset of new response |
| Persist `created_at`, `model_version`, `decision_trace` per decision | PASS | `analytics/recent` smoke includes them |
| API surface documented | PASS | `FINAL_AUDIT.md`, `README.md` |

## Phase 7 — Automated Tests

| Activity | Status | Evidence |
|---|---|---|
| `pytest` + `httpx` dev dependencies installed (venv) | PASS | `pip install -r requirements-dev.txt` |
| `tests/conftest.py` — temp DB + temp model store env override, session-trained model | PASS | 47 tests used it |
| Test suites: auth/RBAC, validation (10 parametrized), rules, decisions/analytics, model lifecycle, predictor/registry/health | PASS | `tests/test_*.py` |
| **Full suite result** | PASS | **47 passed** in 25.49 s |

## Phase 8 — Frontend Redesign

| Activity | Status | Evidence |
|---|---|---|
| React Router SPA with `ProtectedRoute` + role-aware UI | PASS | `App.jsx`, `auth/context.jsx` |
| Axios client with env-configurable base (`VITE_API_BASE_URL` or `/api`), 401 handling | PASS | `api/client.js` |
| Pages: Login, Dashboard, Coordinate, Analytics, ModelInsights, ModelManagement | PASS | `frontend/src/pages/*` |
| Custom, dependency-free charts (donut + bar) and design system | PASS | `components/*`, `styles.css` |
| Vite dev proxy `/api → http://127.0.0.1:8000` (strips prefix) | PASS | verified live: root 200, `/api/health`, `/api/version`, `/api/login` through proxy |
| Nginx prod config with `/api` reverse proxy + SPA fallback + dual-stack listen | PASS | verified in Docker (below) |
| Lint | PASS | `npm run lint` — 0 errors, 0 warnings |
| Production build | PASS | `npm run build` — 299.66 kB JS, 11.14 kB CSS (3 chunks, 5 assets) |

## Phase 9 — Containerization

| Activity | Status | Evidence |
|---|---|---|
| `backend/Dockerfile` rebuilt (ENV for compose injection; non-root runtime practical; excludes dev junk via `.dockerignore`) | PASS | image `paths-backend` built |
| `backend/.dockerignore`, `frontend/.dockerignore` | PASS | build contexts verified during build (tests not shipped) |
| `docker-compose.yml` — backend (env: `DATABASE_URL=sqlite:////app/data/paths.db`, `MODEL_STORE_DIR=/app/model_store`, `JWT_SECRET=${JWT_SECRET:-change-me}`, named volume `paths_data:/app/data`) + frontend on `8080:80` | PASS | verified at runtime |
| `docker compose build` | PASS | both images built (`BUILD_EXIT=0`) |
| `docker compose up` — backend health | PASS | `BACKEND_HEALTH=True db=ok model=v1` |
| Frontend SPA served | PASS | `GET :8080/` → 200, page carries `<title>PATHS` and mount root |
| `/api` proxy through Nginx live | PASS | `:8080/api/health` → `alive:model=v1`; `/api/version` → 2.0.0; `/api/login` → role=admin |
| Clean teardown | PASS | `docker compose down` (containers + network removed; named volume kept) |

### Issues found & fixed during Docker verification
1. **Named volume on a file path**: mounting `paths_db:/app/paths.db` made Docker create a *directory* at that path → SQLite `unable to open database file`. Fixed: named volume `paths_data:/app/data` + `DATABASE_URL=sqlite:////app/data/paths.db`.
2. **Nginx entrypoint hang**: the `nginx:alpine` `10-listen-on-ipv6-by-default.sh` blocked at `apk manifest nginx` in this Docker Desktop runtime, so nginx never launched. Fixed: frontend Dockerfile sets `ENTRYPOINT ["nginx", "-g", "daemon off;"]` to bypass the helper, and `nginx.conf` declares both `listen 80;` and `listen [::]:80;`.

## Phase 10 — Documentation & Final Verification

| Activity | Status | Evidence |
|---|---|---|
| `README.md` rewritten (honest, verified content) | PASS | current file |
| `FINAL_AUDIT.md` verification matrix | PASS | current file |
| `report.md` baseline preserved + `AFTER` section added | PASS | current file |
| Demo scenario results captured live | PASS | `DEMO_SCENARIOS.md` |
| Frontend README replaced (was Vite template boilerplate) | PASS | `frontend/README.md` |
| Secrets scan of tracked files | pass | `grep` for credential patterns; no real secrets in tracked content |
| Stale workaround notes (`counter_run.txt`, `terminal.txt`) removed | PASS | removed and staged (`git rm`); models laid out versioned now, no manual copies needed |
| Orphaned process/port check | PASS | all dev servers stopped and verified (`SERVER_CLEANUP=PASS`, Docker down) |

---

## Final Status

Everything green: **47 backend tests pass; v1 active (acc 0.99 / f1 0.9901); smoke tests (authz, validation, coordinate scenarios, analytics, model lifecycle) pass; frontend lint clean + build passes; dev proxy verified; Docker single-command stack verified end-to-end and torn down.**

Remaining uncommitted by design (user may commit when desired). Runtime-generated files (`.env`, `*.db`, `venv/`, `node_modules/`, `dist/`, model outputs from runs) are git-ignored.