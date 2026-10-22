@echo off
rem ============================================================
rem  ONEAD Assistant RAG - demarrage unifie
rem  Backend FastAPI (:8000) + Frontend Vite (:5173)
rem  Ctrl+C arrete les deux serveurs.
rem ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
echo.
echo Fermeture de la fenetre dans 5 secondes...
timeout /t 5 /nobreak >nul
