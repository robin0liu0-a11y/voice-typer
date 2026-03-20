Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

desktop = WshShell.SpecialFolders("Desktop")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = fso.BuildPath(scriptPath, "start.bat")
iconPath = fso.BuildPath(scriptPath, "promo_image.ico")

Set shortcut = WshShell.CreateShortcut(desktop & "\Voice Typer.lnk")
shortcut.TargetPath = batPath
shortcut.WorkingDirectory = scriptPath
shortcut.Description = "语音打字员 - 按住左Alt说话"

' 如果有图标文件就用，否则用默认
If fso.FileExists(iconPath) Then
    shortcut.IconLocation = iconPath
End If

shortcut.Save
WScript.Echo "桌面快捷方式创建成功: " & desktop & "\Voice Typer.lnk"
