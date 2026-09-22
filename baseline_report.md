# PATHS — Baseline Report (Phase 0)

Collected: 2026-09-22. All values captured from actual execution on the current repository.

## Environment

| Item | Value |
|---|---|
| System Python | 3.12.0 (global `python`) |
| Virtualenv Python | 3.10.0 (`venv/Scripts/python.exe`) |
| Node.js | v24.12.0 |
| npm | 11.6.2 |
| Docker | 29.7.2, context `desktop-linux` (available) |
| Git branch | `main`, up to date with `origin/main` |
| pytest | NOT INSTALLED in venv (needs dev dependency) |

## Repository state

- `git status`: `backend/paths.db` modified; `report.md` untracked.
- No root `.gitignore` exists. Only `frontend/.gitignore`.
- `venv/` is tracked in git (15,003 files). `backend/**/__pycache__/*.pyc` tracked.
- `backend/.env` tracked (contains JWT secret). `backend/paths.db` and root `paths.db` tracked.
- No tests, no CI, no `pyproject.toml`/`setup.py`.

## Backend startup (verified)

Command: `venv/Scripts/python.exe -m uvicorn api.app:app --port 8011` (working dir `backend/`)

- `/health` → `{"status":"alive","environment":"development"}` — HTTP 200
- `/version` → `{"app":"PATHS: The Coordinate Engine","version":"1.0.0"}` — HTTP 200
- Server terminated cleanly after checks. Port 8011 confirmed free afterward.

## Model loading & inference (verified)

Loaded `model_store/v1.pkl` (RandomForestClassifier, 6 features) + `model/scaler.pkl`. Inference works:

- `[85,78,80,5.0,0,3]` → class 0 (ADVANCE), confidence 0.995
- `[45,70,65,3.5,6,9]` → class 1 (HOLD), confidence 0.565

Known defect reproduced: sklearn warns `X does not have valid feature names, but StandardScaler was fitted with feature names` (scaler fitted on DataFrame; inference passes raw numpy array).

## Database (verified)

- Two SQLite files: `backend/paths.db` (7 rows, authoritative runtime DB) and root `paths.db` (9 rows, stale leftover).
- Schema: `decision_logs(id, attendance, internal_marks, assignments, study_hours, backlog_count, stress_level, prediction, action, confidence, reason, triggered_by)`.
- **No timestamp column**, **no model_version column** — confirmed against live schema.
- Contains out-of-range rows (e.g. `stress_level=11`, `study_hours=8.3`) proving no input validation.

## Frontend (verified)

- `npm run build` → PASS (exit 0). Vite 7.3.0, 84 modules, bundle 232.94 kB (76.43 kB gzip), built in 2.75s.
- Existing UI: plain input-styled pages, no routing, no charting, no loading states.

## Test status

- No project tests exist (backend or frontend).
- `pytest` not installed.

## Audit cross-check

Findings of the preceding forensic audit (report.md) were re-verified against the live repository and **match**. The only deltas from the audit: `report.md` untracked (created by audit), `backend/paths.db` dirty (pre-existing). No other discrepancies observed.