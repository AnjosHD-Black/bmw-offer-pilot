# BMW Offer Pilot

Frontend: React  
Backends: FastAPI (G05, G73, Contract)

## Development

### Backend G05
cd backend_g05
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

### Backend G73
cd backend_g73
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

### Backend Contract
cd backend_contract
pip install -r requirements.txt
uvicorn main:app --reload --port 8004

### Frontend
cd frontend
npm install
npm run dev
