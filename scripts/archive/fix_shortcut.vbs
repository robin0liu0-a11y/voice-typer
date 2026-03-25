' 修复桌面快捷方式 - 不显示命令行窗口
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
pyFile = scriptPath & "\voice_typer_glass.py"

Set Shortcut = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\Voice Typer.lnk")
Shortcut.TargetPath = "pythonw.exe"
Shortcut.Arguments = """" & pyFile & """"
Shortcut.WorkingDirectory = scriptPath
Shortcut.Description = "Voice Typer - 语音打字"
Shortcut.WindowStyle = 7
Shortcut.Save

WScript.Echo "[OK] 快捷方式已更新 - 不再显示命令行窗口"
WScript.Echo "路径: " & pyFile
