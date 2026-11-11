@echo off
cd /d "%~dp0"
if not exist "build\webview2\ReportHost.exe" (
  powershell.exe -NoProfile -File "%~dp0Build-WebView2Host.ps1"
  if errorlevel 1 goto setup
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe" (
  start "" "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe" "%~dp0run.py"
  exit /b
)
py -3 -c "import tkinter" >nul 2>&1
if not errorlevel 1 (
  start "" pyw -3 "%~dp0run.py"
  exit /b
)
python run.py
if errorlevel 1 pause
exit /b

:setup
echo Build-WebView2Host.ps1 requires the Microsoft WebView2 SDK.
echo See README.md for build instructions.
pause
exit /b 