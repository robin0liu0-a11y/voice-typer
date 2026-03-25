' Voice Typer 开机启动脚本
' 使用方法：将此文件复制到 Windows 启动文件夹
' Win+R 输入 shell:startup 打开启动文件夹

Set WshShell = CreateObject("WScript.Shell")
scriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pythonw """ & scriptPath & "\voice_typer_glass.py""", 0, False
