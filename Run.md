Commands to run PATHS:
Local dev
# backend
venv\Scripts\Activate.ps1
python -m uvicorn api.app:app --app-dir backend --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev        # http://localhost:5173
Docker (single command)
docker compose up --build   # backend http://localhost:8000, frontend http://localhost:8080
Tests
python -m pytest backend\tests -q