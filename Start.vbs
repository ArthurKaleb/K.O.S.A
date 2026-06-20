Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Apps\S.C.R && python -m http.server 8000", 0
Set WshShell = Nothing