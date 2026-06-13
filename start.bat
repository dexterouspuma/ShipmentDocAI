@echo off
echo Starting ShipmentDocAI...

start "API" cmd /k "cd /d %~dp0api && .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

start "Frontend" cmd /k "cd /d %~dp0web && npm run dev"

echo.
echo ShipmentDocAI started!
echo   API:      http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
