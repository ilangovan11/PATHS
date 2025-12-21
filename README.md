# PATHS
## AI-Powered Student Risk & Decision Intelligence Platform

PATHS (The Coordinate Engine) is an end-to-end **machine learning–driven decision system** that predicts student academic risk levels and produces **interpretable actions** — **ADVANCE**, **HOLD**, or **RETREAT** — using both **ML inference** and **rule-based overrides**.

This repository represents a **production-ready ML system** with:
- Model training & retraining
- Secure JWT-based authentication
- Admin-only analytics & governance
- Persistent decision logging
- React-based frontend dashboard
- Model versioning & lifecycle management

---

## 1. System Overview

PATHS processes structured student indicators:
- Attendance
- Internal marks
- Assignment performance
- Daily study hours
- Backlog count
- Stress level

Using these, it:
1. Predicts a **risk category** using ML
2. Applies **safety & confidence rules**
3. Generates a **transparent decision**
4. Logs the decision for analytics
5. Exposes results through a secure API

---

## 2. Architecture

### Core Layers
- **Data Layer** – Synthetic dataset generation
- **ML Layer** – Training, prediction, retraining
- **Decision Engine** – Rules + confidence thresholds
- **API Layer** – FastAPI services
- **Auth Layer** – JWT-based role security
- **DB Layer** – SQLite decision logging
- **Analytics Layer** – Admin dashboards
- **Frontend** – React + Axios client

---

## 3. Project Structure

PATHS/
│
├── data/
│ ├── raw/
│ │ ├── student_data.csv
│ │ └── generate_data.py
│ └── processed/
│
├── model/
│ ├── trainer.py
│ ├── predictor.py
│ └── scaler.pkl
│
├── model_store/
│ ├── registry.json
│ └── v1.pkl
│
├── training/
│ └── retrain.py
│
├── engine/
│ ├── decision.py
│ └── paths_logic.py
│
├── api/
│ ├── app.py
│ ├── routes.py
│ ├── decision_routes.py
│ ├── analytics_routes.py
│ ├── model_routes.py
│ ├── auth_routes.py
│ └── health.py
│
├── auth/
│ ├── jwt.py
│ ├── security.py
│ └── users.py
│
├── db/
│ ├── database.py
│ └── models.py
│
├── core/
│ └── config.py
│
├── frontend/
│ └── (React + Vite app)
│
├── main.py
├── requirements.txt
├── .env
└── README.md


---

## 4. Machine Learning Pipeline

### Data Generation
- 500 synthetic student records
- Stratified into:
  - ADVANCE (low risk)
  - HOLD (moderate risk)
  - RETREAT (high risk)
- 5% label noise injected for realism

### Preprocessing
- Train–test split with stratification
- StandardScaler fitted **only on training data**
- Scaler persisted for inference consistency

### Model
- RandomForestClassifier
- Class-weighted
- Depth-controlled
- Probabilistic outputs used for confidence

---

## 5. Decision Engine Logic

### Rule Overrides (Priority)
- Attendance < 50 → **RETREAT**
- Backlogs ≥ 5 AND Stress ≥ 8 → **RETREAT**
- Confidence < 0.6 → **HOLD**

### Final Actions
| Prediction | Action | Meaning |
|----------|--------|--------|
| ADVANCE | ADVANCE | Stable performance |
| HOLD | HOLD | Monitor closely |
| RETREAT | RETREAT | High academic risk |

---

## 6. Authentication & Security

- JWT-based authentication
- Roles:
  - `admin` → full access
  - `viewer` → restricted
- Admin-only routes:
  - `/analytics/*`
  - `/model/*`
  - `/coordinate` (logging enabled)

---

## 7. Database & Logging

All decisions are persisted with:
- Input features
- Prediction
- Action
- Confidence
- Reason
- Triggered user
- Timestamp

This enables **auditability & analytics**.

---

## 8. Analytics API

### Available Endpoints
- `/analytics/summary` – Decision counts
- `/analytics/confidence` – Confidence stats
- `/analytics/stress-impact` – Stress vs action distribution

---

## 9. Model Lifecycle Management

- Model registry stored in `model_store/registry.json`
- Active model dynamically loaded
- Supports hot retraining via API
- Versioned model history retained

---

## 10. Frontend (React)

### Pages
- **Login** – JWT authentication
- **Coordinate** – Execute decision
- **Analytics** – Admin intelligence report

### Features
- Axios interceptor for auth
- Live decision rendering
- Secure admin analytics

---

## 11. Environment Variables

`.env`


APP_NAME=PATHS
APP_VERSION=1.0.0
ENV=development

JWT_SECRET=paths_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60


---

## 12. How to Run

1. Train model
2. Start backend
3. Start frontend
4. Login as admin
5. Execute coordinate
6. View analytics
7. Retrain model if needed

---

## 13. Example Output

```json
{
  "prediction": "RETREAT",
  "action": "RETREAT",
  "confidence": 0.87,
  "reason": "Critical risk detected by rule override"
}
