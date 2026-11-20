@echo off
title Subtitties - Создатель субтитров
cd /d "%~dp0"

echo Запуск Subtitties...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Попытка запуска через py launcher...
    py main.py
)
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo   Произошла ошибка при запуске программы.
    echo ========================================================
    pause
)
