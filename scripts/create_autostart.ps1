$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [Environment]::GetFolderPath('Startup')
$Shortcut = $WshShell.CreateShortcut("$StartupPath\VoiceTyper.lnk")
$Shortcut.TargetPath = "D:\Claude Code\voice-typer\start_clean.bat"
$Shortcut.WorkingDirectory = "D:\Claude Code\voice-typer"
$Shortcut.Description = "Voice Typer"
$Shortcut.Save()
Write-Host "OK: $StartupPath\VoiceTyper.lnk"
