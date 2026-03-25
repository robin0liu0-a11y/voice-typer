' 创建 Voice Typer 桌面快捷方式
Set WshShell = WScript.CreateObject("WScript.Shell")

' 获取桌面路径
DesktopPath = WshShell.SpecialFolders("Desktop")
TargetPath = "D:\Claude Code\voice-typer-v2\start_fixed.bat"
WorkingDir = "D:\Claude Code\voice-typer-v2"

' 删除旧快捷方式
Set FSO = CreateObject("Scripting.FileSystemObject")
If FSO.FileExists(DesktopPath & "\Voice Typer.lnk") Then
    FSO.DeleteFile DesktopPath & "\Voice Typer.lnk"
End If

' 创建新快捷方式
Set oLink = WshShell.CreateShortcut(DesktopPath & "\Voice Typer.lnk")
oLink.TargetPath = TargetPath
oLink.WorkingDirectory = WorkingDir
oLink.Description = "Voice Typer v3.5 - Fixed Version"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,70"
oLink.Save

MsgBox "Voice Typer 快捷方式已修复！" & vbCrLf & vbCrLf & _
       "位置: " & DesktopPath & "\Voice Typer.lnk" & vbCrLf & _
       "目标: " & TargetPath & vbCrLf & vbCrLf & _
       "现在可以双击桌面图标启动了！", _
       vbInformation, "Voice Typer 修复完成"

Set oLink = Nothing
Set FSO = Nothing
Set WshShell = Nothing
