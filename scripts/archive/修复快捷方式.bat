@echo off
chcp 65001 >nul
title 修复 Voice Typer 快捷方式
cls

echo ============================================
echo     修复 Voice Typer 桌面快捷方式
echo ============================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "TARGET=D:\Claude Code\voice-typer-v2\start_fixed.bat"
set "WORKDIR=D:\Claude Code\voice-typer-v2"

echo 快捷方式信息:
echo   桌面: %DESKTOP%
echo   目标: %TARGET%
echo   工作目录: %WORKDIR%
echo.

:: 删除旧快捷方式
if exist "%DESKTOP%\Voice Typer.lnk" (
    echo [1/3] 删除旧快捷方式...
    del "%DESKTOP%\Voice Typer.lnk"
) else (
    echo [1/3] 没有找到旧快捷方式
)

:: 创建新快捷方式
echo [2/3] 创建新快捷方式...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\Voice Typer.lnk'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%WORKDIR%'; $s.Description = 'Voice Typer v3.5 - Fixed'; $s.IconLocation = '%%SystemRoot%%\System32\shell32.dll,70'; $s.Save()"

if %errorlevel% == 0 (
    echo [3/3] 完成！
    echo.
    echo ============================================
    echo     修复完成！
    echo ============================================
    echo.
    echo 新快捷方式位置:
    echo   %DESKTOP%\Voice Typer.lnk
    echo.
    echo 现在可以双击桌面快捷方式启动了！
    echo.
    echo 快捷键:
    echo   左 Alt     = 语音打字
    echo   Alt + V    = 语音存笔记
    echo   ESC        = 退出
    echo.
) else (
    echo [ERR] 快捷方式创建失败
    echo.
    echo 手动创建方法:
    echo 1. 右键桌面 -^> 新建 -^> 快捷方式
    echo 2. 位置: D:\Claude Code\voice-typer-v2\start_fixed.bat
    echo 3. 起始位置: D:\Claude Code\voice-typer-v2
    echo.
)

pause
