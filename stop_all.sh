#!/bin/zsh
set -e

for pid in $(lsof -t -iTCP:8001 -sTCP:LISTEN 2>/dev/null); do kill "$pid" 2>/dev/null || true; done
for pid in $(lsof -t -iTCP:8002 -sTCP:LISTEN 2>/dev/null); do kill "$pid" 2>/dev/null || true; done
for pid in $(lsof -t -iTCP:8003 -sTCP:LISTEN 2>/dev/null); do kill "$pid" 2>/dev/null || true; done
for pid in $(lsof -t -iTCP:5173 -sTCP:LISTEN 2>/dev/null); do kill "$pid" 2>/dev/null || true; done
pkill -f 'uvicorn main:app' 2>/dev/null || true
pkill -f 'vite --host 127.0.0.1 --port 5173' 2>/dev/null || true
pkill -f 'vite --host 0.0.0.0 --port 5173' 2>/dev/null || true

echo "Alle Server gestoppt."
