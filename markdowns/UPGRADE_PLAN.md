# PATHS 2.0 — Upgrade Plan

Based on the verified baseline (baseline_report.md) and forensic audit (report.md). Every proposed change is grounded in a verified repository defect.

## 1. Current architecture (verified)

```
React SPA → axios (hard-coded 127.0.0.1:8000) → FastAPI
  → POST /login (plaintext users dict + JWT HS256)
  → POST /coordinate (admin only) → engine.coordinate()
        → predictor.predict()   (RandomForest predict_proba; scaler mismatch warning)
        → paths_logic.resolve_action()  (2 override rules + confidence gate)
        → DecisionLog insert (no timestamp, no model_version)
  → GET /analytics/* (admin only)   → SQLite aggregates
  → POST /model/retrain (subprocess) → rewrites model_store/vN.pkl + registry
        (in-memory model cache NOT refreshed after retrain)
```

## 2. Current working features (verified)

- Login + JWT + role check (admin/viewer)
- `/coordinate` ML+rule decision with logging
- Analytics endpoints (summary, confidence, stress-impact)
- `/model/retrain`, `/model/status`
- `/health`, `/version`
- Frontend login / coordinate / analytics screens; production build passes
- Docker compose (backend + frontend/nginx); Docker available in environment
- SQLite persistence; model registry `model_store/registry.json`

## 3. Current problems (verified)

| # | Problem | Evidence |
|---|---|---|
| 1 | Plaintext passwords in `auth/users.py` | file read |
| 2 | Committed `backend/.env` with `JWT_SECRET=paths_secret_key` | file read + git tracked |
| 3 | No root `.gitignore`; `venv/` + `__pycache__` + `.db` + `.env` tracked | `git ls-files` |
| 4 | No input validation; model extrapolates on nonsense | DB rows `stress_level=11`, `study_hours=8.3` |
| 5 | Scaler feature-name warning at inference | reproduced in baseline |
| 6 | `decision_logs` has no timestamp / model_version | live schema |
| 7 | Retrain uses different hyperparams than base trainer | `trainer.py` vs `retrain.py` |
| 8 | Retrain does not refresh in-memory serving model | `predictor.py` module-global cache |
| 9 | Registry has no metrics/metadata/history; only `active_model` | `registry.json` |
| 10 | No decision trace / explanation beyond static reason string | `engine/*` |
| 11 | Error handling exposes no consistent JSON contract | routes raise raw |
| 12 | Frontend is unpolished, no routing, no states, no charts, responsive/hard-coded URL | source review |
| 13 | No tests, no lint | repo scan, pytest absent |
| 14 | `main.py` body commented out; `utils/metrics.py` empty; `processed.csv` empty | file reads |
| 15 | Docker nginx has no `/api` proxy; frontend API URL hard-coded | `nginx.conf`, `client.js` |
| 16 | Root `paths.db` stale duplicate vs `backend/paths.db` | DB counts 9 vs 7 |

## 4. Proposed changes

**Preserved:** Random Forest + StandardScaler, 6 raw features, 3 classes, hybrid rule layer, JWT roles, SQLite, FastAPI, React/Vite, Docker. No new ML framework; no LLM; no feature engineering (unjustified — see §5).

1. **Hygiene (Phase 1):** root `.gitignore`; untrack `venv/`, `__pycache__`, `.db`, `.env`; add `.env.example`. Keep model artifacts tracked (required by app + Docker image). Decision on duplicate DB recorded: `backend/paths.db` authoritative; root copy kept on disk but no longer tracked; both migrated.
2. **Security (Phase 2):** bcrypt-hashed passwords in a `users` table (seeded at startup, existing credentials preserved), JWT secret from env with warning if absent, no secrets committed.
3. **Validation (Phase 3):** document + enforce ranges at API boundary (Pydantic) and frontend.
4. **ML hardening (Phase 4):** explicit `FEATURE_ORDER`, versioned scaler+model+metrics+metadata under `model_store/vN/`, single `MODEL_CONFIG`, shared train&retrain pipeline, real evaluation (accuracy/precision/recall/F1/confusion), promotion policy (activate only if not worse), safe hot reload (cache invalidation keyed on active model), confidence documented as max class probability, uncalibrated.
5. **Explainability (Phase 5):** decision trace steps returned from actual execution; model feature importance served from model object; rules_checked list.
6. **Database (Phase 6):** migration adds `created_at`, `model_version`, `decision_trace` to `decision_logs`; preserves existing rows; runs safely at startup.
7. **Analytics:** keep existing endpoints; add `/analytics/recent` for dashboard; all data real.
8. **Frontend (Phase 8):** full redesign — Dashboard, Coordinate, Analytics, Model Insights, Model Management; react-router routing; configurable API base (`VITE_API_BASE_URL`, `/api` in Docker); loading/error/empty states; CSS-native charts (no new deps); responsive; accessible.
9. **Docker (Phase 9):** nginx `/api` reverse proxy → FastAPI; backend server-side nginx config; verify build+run.
10. **Tests (Phase 7):** pytest + httpx TestClient, temp DB/model-store via env overrides.
11. **Docs (Phase 10):** rewrite README; create FINAL_AUDIT.md; update report.md (BEFORE/AFTER).

## 5. Feature engineering decision

**NOT ADDED.** The 6 existing features already produce 0.99 test accuracy on the synthetic data (previously measured; re-measured in Phase 4 from actual training). Derived features (academic score, workload, stress-adjusted performance) would add train/inference surface and explanation burden without meaningful, verifiable performance gain. Documented rationale kept in README **Limitations** and this plan.

## 6. Files expected to change

- `backend/main.py`, `backend/api/*.py`, `backend/auth/*.py`, `backend/core/*.py`, `backend/db/*.py`, `backend/engine/*.py`, `backend/model/*.py`, `backend/training/retrain.py`, `backend/utils/preprocess.py`, `backend/utils/metrics.py` (implemented), `backend/requirements.txt`
- `frontend/src/**` (all), `frontend/package.json` (scripts), `frontend/vite.config.js`, `frontend/nginx.conf`, `frontend/index.html`
- `docker-compose.yml`, root `README.md`, root `.gitignore`, `.env.example`
- `report.md`, `FINAL_AUDIT.md`, `UPGRADE_PROGRESS.md` (add)

## 7. Files expected to be added

- `backend/tests/` (auth, authorization, validation, inference, rules, trace, analytics, model status, retrain, persistence)
- `backend/api/__init__.py` metering not needed; `backend/core/logging.py`; `backend/db/migration.py`; `backend/model/registry.py`; `backend/requirements-dev.txt`
- `frontend/src/components/`, pages (Dashboard, ModelInsights, ModelManagement), context, charts
- `.env.example`, `UPGRADE_PLAN.md`, `UPGRADE_PROGRESS.md`, `FINAL_AUDIT.md`, `baseline_report.md`

## 8. Files expected to be removed (after verification)

- `backend/utils/metrics.py` content replaced (implemented, not deleted)
- Obsolete model artifacts after new versioned store: `backend/model/paths_model.pkl`, `backend/model/scaler.pkl`, `backend/model_store/v1.pkl` (regenerable; superseded by `model_store/v1/model.pkl` + `scaler.pkl` + `metrics.json` + `metadata.json`)
- Empty `frontend/public`, `frontend/src/assets` (empty dirs, no tracked content — verify first)
- `data/processed/processed.csv` (0 bytes, never written by pipeline) — replaced by generated metrics; verify no references first

## 9. Risks

| Risk | Mitigation |
|---|---|
| Retrain promotion policy could deactivate a working model | Default `auto_promote` false; explicit activate endpoint with confirmation |
| Migration could fail on root `paths.db` | Idempotent `ADD COLUMN` guarded by pragma table_info; failure logged, startup continues |
| Frontend redesign breaks the working flow | Preserve endpoints/contracts; build + smoke test after each frontend step |
| Docker build time/environment limits | Build images deterministically; if blocked, mark BLOCKED with evidence |
| Venv lacks pytest/httpx | `pip install -r requirements-dev.txt` (documented, expected dependency addition) |

## 10. Validation plan

Per phase: run tests → lint → start affected component → hit endpoints → verify → stop and cleanup. Full matrix at the end in FINAL_AUDIT.md.

## 11. Rollback considerations

- No git history rewrite; all changes remain in working tree / new commits on `main` only if instructed.
- Untracking (`git rm --cached`) is reversible via `git reset`; files remain on disk.
- DB migration is additive-only (new columns), never drops data.
- Old model artifacts kept until new structure verified; both .pkl generated values reproducible via trainer.