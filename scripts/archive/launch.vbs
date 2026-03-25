' Voice Typer 启动脚本
' 完全自包含，不依赖其他文件

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 获取脚本所在目录
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' 使用完整路径启动 pythonw
pythonwPath = "C:\Users\w\AppData\Local\Python\bin\pythonw.exe"
pyFile = scriptPath & "\voice_typer_glass.py"

' 后台运行，不等待
WshShell.Run """" & pythonwPath & """ """ & pyFile & """", 0, False
