@echo off
setlocal

set "ROOT=%~dp0"

start "Arclat Stack" cmd /k "cd /d ""%ROOT%"" && docker compose up --build"
start "Arclat Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm install && npm run dev"

endlocal