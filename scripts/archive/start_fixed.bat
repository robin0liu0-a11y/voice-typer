@echo off
chcp 65001 >nul
title Voice Typer v3.5
cd /d "%~dp0"

echo [Voice Typer] Starting...
echo [Voice Typer] Working directory: %cd%

:: 检查 coli
where coli >nul 2>&1
if %errorlevel% neq 0 (
    echo [Voice Typer] Warning: coli not found in PATH
    echo [Voice Typer] Adding npm global to PATH...
    set "PATH=%PATH%;%APPDATA%\npm"
)

:: 检查是否已有实例运行
echo [Voice Typer] Checking for running instances...

:: 启动 Voice Typer
python voice_typer_glass.py

if %errorlevel% neq 0 (
    echo [Voice Typer] Exited with error code %errorlevel%
    pause
)
