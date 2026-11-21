@echo off
chcp 65001 >nul
title MOZA Integration - Install Python dependencies
echo ================================================
echo   MOZA Integration - Dependency installation
echo ================================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11 64-bit first.
  pause
  exit /b 1
)
py -3.11 --version
if errorlevel 1 (
  echo Python 3.11 not found. Install Python 3.11 64-bit first.
  pause
  exit /b 1
)
echo.
echo Updating pip...
py -3.11 -m pip install --upgrade pip
if errorlevel 1 goto error
echo.
echo Installing required packages...
py -3.11 -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto error
echo.
echo Installation completed successfully.
pause
exit /b 0
:error
echo.
echo Installation failed. Check the error messages above.
pause
exit /b 1
