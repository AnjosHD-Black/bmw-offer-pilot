@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "%ROOT%logs" mkdir "%ROOT%logs"

if exist "%ROOT%.venv\Scripts\activate.bat" (
    call "%ROOT%.venv\Scripts\activate.bat"
) else (
    echo Virtuelle Umgebung nicht gefunden: %ROOT%.venv\Scripts\activate.bat
    echo Bitte zuerst die Python-Umgebung auf dem Windows-Laptop anlegen.
    pause
    exit /b 1
)

start "G05 Backend" /min cmd /c "cd /d ""%ROOT%backend_g05"" && uvicorn main:app --host 127.0.0.1 --port 8001 > ""%ROOT%logs\backend_g05.log"" 2>&1"
start "G73 Backend" /min cmd /c "cd /d ""%ROOT%backend_g73"" && uvicorn main:app --host 127.0.0.1 --port 8002 > ""%ROOT%logs\backend_g73.log"" 2>&1"
start "Contract Backend" /min cmd /c "cd /d ""%ROOT%backend_contract"" && uvicorn main:app --host 127.0.0.1 --port 8003 > ""%ROOT%logs\backend_contract.log"" 2>&1"
start "Frontend" /min cmd /c "cd /d ""%ROOT%frontend"" && npm run dev -- --host 127.0.0.1 --port 5173 > ""%ROOT%logs\frontend.log"" 2>&1"

ping 127.0.0.1 -n 3 > nul
start "" http://127.0.0.1:5173

echo Server gestartet.
echo Frontend: http://127.0.0.1:5173
echo Backend G05: http://127.0.0.1:8001
echo Backend G73: http://127.0.0.1:8002
echo Backend Contract: http://127.0.0.1:8003
pause
