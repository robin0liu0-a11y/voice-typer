$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Voice Typer.lnk")
$Shortcut.TargetPath = "D:\Claude Code\voice-typer\start.bat"
$Shortcut.WorkingDirectory = "D:\Claude Code\voice-typer"
$Shortcut.Description = "Voice Typer 语音输入"
$Shortcut.IconLocation = "D:\Claude Code\voice-typer\assets\icon.ico"
$Shortcut.Save()
Write-Host "OK: $DesktopPath\Voice Typer.lnk"
