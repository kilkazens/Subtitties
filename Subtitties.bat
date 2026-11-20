@echo off
title Subtitties - AI Subtitle Editor
cd /d "%~dp0"
start "" pythonw app.py
if %errorlevel% neq 0 (
    echo Starting Subtitties in console mode...
    python app.py
    pause
)
