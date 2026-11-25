@echo off
title SARA AI Assistant Launcher
color 0B
echo ========================================================
echo        SARA (Smart AI Responsive Assistant)
echo              Launching Systems...
echo ========================================================
echo.

:: 1. Check if Ollama is installed
where ollama >nul 2>nul
if "%ERRORLEVEL%"=="0" (
    tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo [OK] Ollama AI daemon is running.
    ) else (
        echo [INFO] Starting Ollama AI daemon in background...
        start /min "" ollama serve
        timeout /t 3 /nobreak >nul
    )
) else (
    echo [WARNING] Ollama AI is not installed yet.
    echo [INFO] SARA will launch in System-Command mode.
    echo [INFO] To enable AI brain, download Ollama from https://ollama.com
    echo.
)

echo [INFO] Launching SARA Desktop HUD...
echo.

:: 2. Launch main application
cd /d "%~dp0"
python app.py

pause
