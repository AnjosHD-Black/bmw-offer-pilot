# Fuhrpark

Monorepo mit React/Vite Frontend und FastAPI Backend.

## Backend starten
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Swagger Docs: http://localhost:8000/docs

## Frontend starten
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173
