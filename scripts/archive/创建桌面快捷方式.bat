@echo off
chcp 65001 >nul
title Voice Typer - 创建桌面快捷方式

echo ============================================
echo     Voice Typer v3.5 - 创建快捷方式
echo ============================================
echo.

:: 删除旧快捷方式
if exist "%USERPROFILE%\Desktop\Voice Typer.lnk" (
    del "%USERPROFILE%\Desktop\Voice Typer.lnk"
    echo [OK] 已删除旧快捷方式
)

:: 使用 PowerShell 创建新快捷方式
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $lnk = $ws.CreateShortcut($desktop + '\Voice Typer.lnk'); $lnk.TargetPath = 'D:\Claude Code\voice-typer-v2\start.bat'; $lnk.WorkingDirectory = 'D:\Claude Code\voice-typer-v2'; $lnk.IconLocation = '%SystemRoot%\System32\shell32.dll,70'; $lnk.Description = 'Voice Typer v3.5'; $lnk.Save(); Write-Host '快捷方式创建成功!'"

echo.
echo ============================================
echo 桌面快捷方式已创建/修复！
echo ============================================
echo.
echo 启动文件: start.bat
echo 快捷键: 左 Alt = 语音打字
echo.
pause
