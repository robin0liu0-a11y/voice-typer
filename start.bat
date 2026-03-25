@echo off

netstat -ano | findstr ":51234" >nul 2>&1
if %errorlevel%==0 (
    powershell -Command "[System.Windows.Forms.MessageBox]::Show('Voice Typer is already running! Hold Left Alt to record', 'Voice Typer', 'OK', 'Information')"
    exit /b 0
)

cd /d "%~dp0"
start "" /b "C:\Users\w\AppData\Local\Python\bin\pythonw.exe" "%~dp0voice_typer_glass.py"

timeout /t 2 /nobreak >nul
netstat -ano | findstr ":51234" >nul 2>&1
if %errorlevel%==0 (
    powershell -Command "[System.Windows.Forms.MessageBox]::Show('Voice Typer Started! Hold Left Alt to record', 'Voice Typer', 'OK', 'Information')"
) else (
    powershell -Command "[System.Windows.Forms.MessageBox]::Show('Failed to start!', 'Voice Typer', 'OK', 'Error')"
)
