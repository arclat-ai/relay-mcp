@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_PY=%ROOT%backend\venv\Scripts\python.exe"

start "Arclat Infra" cmd /k "cd /d ""%ROOT%"" && docker compose up db redis"

if exist "%BACKEND_PY%" (
    start "Arclat Backend" cmd /k "cd /d ""%ROOT%backend"" && ""%BACKEND_PY%"" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
) else (
    start "Arclat Backend" cmd /k "cd /d ""%ROOT%backend"" && py -3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
)

start "Arclat Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm install && npm run dev"

endlocal