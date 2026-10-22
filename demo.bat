@echo off
rem ============================================================
rem  ONEAD Assistant RAG - mode demonstration
rem  1 seul processus, 1 seule origine : http://127.0.0.1:8000
rem  (build React + FastAPI qui sert l'API et l'interface)
rem  Ctrl+C arrete le serveur.
rem ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -Single
echo.
echo Fermeture de la fenetre dans 5 secondes...
timeout /t 5 /nobreak >nul
