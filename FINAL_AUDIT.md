# PATHS 2.0 — Final Verification Audit

**Target:** upgraded PATHS repo at `D:\1. PROJECTS-MAIN\1. ILA\PATHS`
**Date:** 2026-09-22
**Method:** every row below was produced by an actual executed check (unit tests, live HTTP smoke tests, CLI runs, builds, or container runtime verification). Statuses: `PASS` / `FAIL` / `BLOCKED` / `NOT VERIFIED` / `SKIPPED`. No git commits were created during the upgrade.

> Baseline = the pre-upgrade state; see `baseline_report.md` (read-only forensic audit) and `report.md` (BEFORE → AFTER).

---

## 1. Verification Matrix

| # | Area | Check | Status | Evidence |
|---|---|---|---|---|
| 1 | ML model | v1 trained through the new single pipeline; active in registry | PASS | `model_store/registry.json` → `active_model=v1`; `/model/status` |
| 2 | ML metrics | metrics persisted and exposed (accuracy, f1, per-class, confusion) | PASS | `model_store/v1/metrics.json`: accuracy **0.99**, f1_macro **0.9901**, 100 eval rows, confusion [[28,0,0],[1,41,0],[0,0,30]] |
| 3 | ML inference | no feature-name warnings; deterministic seeding | PASS | repeated CLI inference clean; `random_state=42` |
| 4 | ML versioning | registry history + inactive candidate promotion policy | PASS | `/model/versions` history=1; `PROMOTION_TOLERANCE=0.01` in `model/config.py`; unit tests |
| 5 | Hot reload | serving model flushes on retrain/activate; version-pinned inference | PASS | `model/predictor.py` mtime/version watch + `flush()`; retrain E2E test |
| 6 | Rules | baseline rule semantics preserved (override → gate → map) | PASS | `engine/paths_logic.py`; `test_rules.py`; live scenarios |
| 7 | Input validation | all 6 features range-bounded; bad input → 422 | PASS | `test_validation.py` (10 parametrized cases) + live smoke |
| 8 | Auth | bcrypt-hashed users; JWT issued only on correct creds | PASS | DB `users` bcrypt digests; `/login` admin+viewer smoke |
| 9 | RBAC | no token → 401; viewer coordinate → 403; viewer analytics/model reads → 200 | PASS | smoke + `test_auth.py`, `test_decisions.py` |
| 10 | DB | additive schema migration (timestamp, model_version, trace, users) on existing DB | PASS | `ensure_schema`; `/analytics/recent` rows carry `created_at` + `model_version`; prior 7 rows preserved (total 10) |
| 11 | Decision trace | `/coordinate` returns superset: probabilities, feature_importances, rules_checked, trace, model_version | PASS | live smoke + README example verified against real output |
| 12 | Analytics | summary/confidence/stress-impact/recent return real aggregates | PASS | live: summary total 10 = ADVANCE 3 / HOLD 4 / RETREAT 3; recent rows logged with `created_at` + `model_version` |
| 13 | Backend tests | full pytest suite | PASS | **47 passed** (25.49 s) |
| 14 | Frontend lint | `npm run lint` | PASS | 0 errors, 0 warnings |
| 15 | Frontend build | `npm run build` | PASS | 299.66 kB JS, 11.14 kB CSS; Vite 7, React 19 |
| 16 | Dev `/api` proxy | Vite proxy → backend (health/version/login) | PASS | live controlled run: root 200, `/api/health` alive, `/api/version` 2.0.0, `/api/login` admin |
| 17 | Docker build | `docker compose build` both images | PASS | `BUILD_EXIT=0` |
| 18 | Docker runtime | backend health in container; SPA served; `/api` proxy; login through nginx | PASS | `db=ok model=v1` @:8000; root 200 with `PATHS` title @:8080; `/api/health`, `/api/version`, `/api/login` all PASS |
| 19 | Docker persistence | DB on named volume (`paths_data:/app/data`) | PASS | runtime exercised; teardown clean |
| 20 | Docker teardown | `docker compose down` | PASS | containers + network removed |
| 21 | Secrets in repo | no real secrets in tracked files | PASS | `.env.example` only placeholders; JWT secret default ephemeral; `.env`/`*.db` untracked |
| 22 | Repo hygiene | venv/DBs/env/`__pycache__` untracked; root `.gitignore` active | PASS | `git status` review |

## 2. Demo Scenarios (live, recorded)

| Scenario | Input | Result | Verified |
|---|---|---|---|
| A. Healthy student → ADVANCE | `[90, 85, 88, 6, 0, 3]` | ADVANCE, conf **0.9991** | live CLI + smoke |
| B. Critical risk → RETREAT override | `[40, 60, 55, 2, 6, 9]` | RETREAT, rule override | live |
| C. Low confidence (no override) → HOLD | `[50, 70, 65, 3, 4, 7]` | HOLD, conf **0.57** (< 0.6 gate) | live |
| D. Invalid input → 422 | `stress_level = 11` | 422 with field detail | smoke + unit tests |

Full outputs: `DEMO_SCENARIOS.md`.

## 3. What Was FIXED vs the Baseline

| Baseline finding | Status after upgrade |
|---|---|
| No tests anywhere | **47 pytest tests**, all passing |
| `venv/` + `__pycache__` + binaries + `.env` committed; no root `.gitignore` | untracked; `.gitignore` added; `.env.example` provided |
| Plaintext passwords; `passlib` unused; committed JWT secret | bcrypt hashes; secret rotation to ephemeral default; no committed secrets |
| No input validation; out-of-range extrapolation in DB | Pydantic ranges → 422; defect closed |
| No log timestamp; metrics never persisted/exposed | `created_at` + `model_version` columns; `metrics.json` + `/model/status` |
| `/coordinate` not machine-readable | superset response (probabilities, importances, rules_checked, trace, model_version) |
| Retrain hyperparameter mismatch + no hot-swap | single shared `MODEL_CONFIG`; promotion gate; hot reload flush |
| `utils/metrics.py` empty, `processed.csv` empty, commented `main.py` | rewritten/removed; `main.py` is the runner |
| react-router-dom unused; manual page switching | full React Router SPA with protected routes |
| frontend hard-coded `127.0.0.1:8000`; no nginx `/api` proxy | `VITE_API_BASE_URL`; dev + nginx proxy both verified |
| stale `counter_run.txt` / `terminal.txt` workaround notes | retired (removed) during final hygiene |

## 4. Remaining / Accepted Limitations

- Synthetic dataset with 5% noise; 0.99 accuracy is on the synthetic holdout, not real-world data.
- Confidence is uncalibrated `max(predict_proba)`; 0.6 gate is heuristic.
- Rules are code; changing them requires a code change + tests.
- SQLite is single-writer; suited to light deployments, not high-concurrency production.
- No CI pipeline, no API rate-limiting, no TLS termination at the app layer (deploy behind a TLS proxy).
- Docker verification uses default demo/`change-me` secret semantics; a strong `JWT_SECRET` is required for any long-lived deployment.
- Root-level `paths.db` (older layout) and `backend/.env` remain on disk as untracked local residue, not part of the product.

## 5. Honest Status Table

| Capability | Status |
|---|---|
| Train / retrain / version / promote / activate | PASS |
| Hybrid decision (ML + rules + confidence gate) | PASS |
| Decision trace / explainability metadata | PASS |
| Secure auth + role-based access | PASS |
| Input validation | PASS |
| Analytics | PASS |
| Migration of existing data | PASS |
| Full test suite | PASS (47) |
| Frontend SPA + charts | PASS |
| Dev proxy / production nginx proxy | PASS / PASS |
| Docker single-command deployment | PASS |
| Documentation | PASS (this + README + DEMO_SCENARIOS + UPGRADE_PROGRESS) |

**Overall: PASS** — PATHS 2.0, verified in every phase, honestly documented, no unverified claims in the final documentation.