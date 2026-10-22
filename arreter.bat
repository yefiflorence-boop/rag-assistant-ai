@echo off
rem ============================================================
rem  ONEAD Assistant RAG - arret du backend et du frontend
rem ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
pause
