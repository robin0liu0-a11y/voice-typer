@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Voice Typer v3.2
cls
python voice_typer_glass.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败
    pause
)
