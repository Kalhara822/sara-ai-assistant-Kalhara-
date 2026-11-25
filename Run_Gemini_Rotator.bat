@echo off
title Gemini API Key Rotator Proxy Server
echo ========================================================
echo        Gemini API Key Rotator Proxy Server
echo                 Launching Server...
echo ========================================================
echo.

cd /d "%~dp0\gemini-api-key-rotator-proxy-server"

python -m uvicorn main:APP --host 127.0.0.1 --port 8000 --reload

pause
