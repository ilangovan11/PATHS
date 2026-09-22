# PATHS Frontend

React 19 + Vite dashboard for PATHS (The Coordinate Engine).

## Commands

```bash
npm install
npm run dev      # http://localhost:5173 — dev server + /api proxy → http://127.0.0.1:8000
npm run lint     # ESLint (0 errors, 0 warnings)
npm run build    # production build → dist/
npm run preview  # preview the production build
```

## API base URL

The axios client reads `VITE_API_BASE_URL` (see `.env.example`).

- **Dev:** left unset → the client calls `/api/...`, which the Vite dev server proxies to the backend at `http://127.0.0.1:8000`, stripping the `/api` prefix (see `vite.config.js`).
- **Prod (Docker):** Nginx serves the SPA and applies the same `/api → backend:8000` proxy (see `nginx.conf`), so the page and API share one origin — no CORS needed.

## Pages

| Route | Access | Description |
|---|---|---|
| `/login` | public | email + password → JWT |
| `/` | authenticated | dashboard: model vitals, recent decisions |
| `/coordinate` | authenticated | evaluate a student profile (submit requires admin) |
| `/analytics` | authenticated | decision counts, confidence, stress impact |
| `/model` | authenticated | active model metrics, feature importances, versions |
| `/model/manage` | admin | retrain / activate model versions |

Auth is handled by `auth/AuthContext.jsx` (token + role persisted in `localStorage`); an axios interceptor attaches the Bearer token and broadcasts a `401` event on expiry. Route guards live in `components/ProtectedRoute.jsx`.

## Styling & charts

No CSS framework and no charting library — a small design system lives in `styles.css`, and the donut/bar charts are custom SVG components (`components/DonutChart.jsx`, `components/BarChart.jsx`).

## Build

Production build (2026-09-22): **299.66 kB** JS, **11.14 kB** CSS — PASS; lint clean — PASS. Verified serving through both the dev proxy and the Docker Nginx proxy (see `FINAL_AUDIT.md`).