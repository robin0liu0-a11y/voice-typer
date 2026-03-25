Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

shortcutPath = "C:\Users\w\Desktop\Voice Typer.lnk"
Set shortcut = WshShell.CreateShortcut(shortcutPath)

shortcut.TargetPath = "D:\Claude Code\voice-typer-v2\start_clean.bat"
shortcut.WorkingDirectory = "D:\Claude Code\voice-typer-v2"
shortcut.Description = "Voice Typer"
shortcut.WindowStyle = 7
shortcut.Save

WScript.Echo "OK"
