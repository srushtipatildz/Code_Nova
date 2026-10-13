@echo off
title MayI - AI Agent Consent Layer
echo ========================================================
echo   MayI - Local Consent Layer for AI Agents
echo ========================================================
echo.
echo Starting Python Web Server on http://localhost:8000 ...
echo (If using local AI, ensure Ollama is running with qwen2.5:3b)
echo.
start http://localhost:8000/demo/index.html
python server.py
pause
