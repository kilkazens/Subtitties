@echo off
echo ============================================
echo   Subtitties - Установка зависимостей
echo ============================================
echo.

python -m pip install --upgrade pip
pip install customtkinter Pillow opencv-python-headless imageio-ffmpeg

echo.
echo Установка faster-whisper (распознавание речи)...
pip install faster-whisper

echo.
echo ============================================
echo   Установка завершена!
echo   Запуск: python main.py
echo ============================================
echo.
pause
