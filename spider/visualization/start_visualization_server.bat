@echo off
setlocal

cd /d "%~dp0..\.."
set "HOST=127.0.0.1"
set "PORT=8765"
set "URL=http://%HOST%:%PORT%/spider/visualization/index.html"

echo Starting FSG/FSAE visualization server...
echo URL: %URL%
echo.

start "" "%URL%"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -m http.server %PORT% --bind %HOST%
  goto :done
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python -m http.server %PORT% --bind %HOST%
  goto :done
)

echo Python was not found. Please install Python or start a static server in this folder.
pause

:done
endlocal
