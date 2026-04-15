@echo off

:: 自动清理旧的 VoiceTyper.exe 实例（如果有）
tasklist /FI "IMAGENAME eq VoiceTyper.exe" 2>NUL | find /I "VoiceTyper.exe" >NUL
if %errorlevel%==0 (
    taskkill /IM VoiceTyper.exe /F >NUL 2>&1
    timeout /t 1 /nobreak >NUL
)

:: 检查端口是否被占用（python 实例）
netstat -ano | findstr ":51234" >NUL 2>&1
if %errorlevel%==0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":51234"') do (
        taskkill /PID %%a /F >NUL 2>&1
    )
    timeout /t 1 /nobreak >NUL
)

cd /d "%~dp0"
start "" /b "C:\Users\w\AppData\Local\Python\bin\pythonw.exe" "%~dp0voice_typer_glass.py"

timeout /t 2 /nobreak >NUL
netstat -ano | findstr ":51234" >NUL 2>&1
if %errorlevel%==0 (
    powershell -Command "[System.Windows.Forms.MessageBox]::Show('Voice Typer v3.8 Started! Hold RightAlt to record, RightAlt+M for note', 'Voice Typer', 'OK', 'Information')"
) else (
    powershell -Command "[System.Windows.Forms.MessageBox]::Show('Failed to start! Check voice_typer.log', 'Voice Typer', 'OK', 'Error')"
)
