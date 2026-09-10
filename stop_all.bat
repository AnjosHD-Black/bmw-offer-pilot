@echo off
setlocal

for /f "tokens=5" %%i in ('netstat -ano ^| findstr /R /C:":8001 " /C:":8002 " /C:":8003 " /C:":5173 "') do (
    taskkill /F /PID %%i >nul 2>&1
)

echo Alle Server gestoppt.
pause
