#!/bin/zsh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

source .venv/bin/activate

mkdir -p "$ROOT/logs"

# Start backend services
(
  cd "$ROOT/backend_g05"
  nohup uvicorn main:app --host 127.0.0.1 --port 8001 > "$ROOT/logs/backend_g05.log" 2>&1 &
) &

(
  cd "$ROOT/backend_g73"
  nohup uvicorn main:app --host 127.0.0.1 --port 8002 > "$ROOT/logs/backend_g73.log" 2>&1 &
) &

(
  cd "$ROOT/backend_contract"
  nohup uvicorn main:app --host 127.0.0.1 --port 8003 > "$ROOT/logs/backend_contract.log" 2>&1 &
) &

# Start frontend
(
  cd "$ROOT/frontend"
  nohup npm run dev -- --host 127.0.0.1 --port 5173 > "$ROOT/logs/frontend.log" 2>&1 &
) &

sleep 2
open "http://127.0.0.1:5173"

echo "Server gestartet."
echo "Frontend: http://127.0.0.1:5173"
echo "Backend G05: http://127.0.0.1:8001"
echo "Backend G73: http://127.0.0.1:8002"
echo "Backend Contract: http://127.0.0.1:8003"
