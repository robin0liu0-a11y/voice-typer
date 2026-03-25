$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\Voice Typer.lnk")
$Shortcut.TargetPath = "D:\Claude Code\voice-typer-v2\start.bat"
$Shortcut.WorkingDirectory = "D:\Claude Code\voice-typer-v2"
$Shortcut.Description = "Voice Typer"
$Shortcut.Save()
Write-Host "Shortcut created: $Desktop\Voice Typer.lnk"
