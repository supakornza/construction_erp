@echo off
setlocal EnableExtensions

REM ============================================================
REM   Construction ERP - Windows launcher
REM   Double-click this file to start the local web application.
REM ============================================================

chcp 65001 >nul
cd /d "%~dp0"
title Construction ERP - Local Web App

set "APP_URL=http://127.0.0.1:8000/"
set "VENV_DIR=%~dp0venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo ============================================================
echo   Construction ERP - Local Web App
echo ============================================================
echo.

REM 1) Create the virtual environment when it is not present.
if not exist "%VENV_PYTHON%" (
  echo [..] Python virtual environment was not found.
  echo [..] Creating it now...
  echo.

  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv "%VENV_DIR%"
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo [X] Python is not installed.
      echo.
      echo     Install Python 3.11 or newer, then run this file again.
      echo     The Python download page will open now.
      timeout /t 2 /nobreak >nul
      start "" "https://www.python.org/downloads/windows/"
      echo.
      pause
      exit /b 1
    )
    python -m venv "%VENV_DIR%"
  )

  if errorlevel 1 (
    echo.
    echo [X] Could not create the Python virtual environment.
    pause
    exit /b 1
  )
)

for /f "delims=" %%v in ('"%VENV_PYTHON%" --version 2^>^&1') do echo [OK] %%v

REM 2) Install dependencies only when the application packages are missing.
"%VENV_PYTHON%" -c "import django, rest_framework, crispy_forms, openpyxl, reportlab" >nul 2>nul
if errorlevel 1 (
  echo [..] Installing application components. This can take a few minutes...
  echo.
  "%VENV_PYTHON%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo [X] Component installation failed.
    echo     Check your internet connection and Python version, then try again.
    pause
    exit /b 1
  )
)
echo [OK] Application components are available.

REM 3) Create the local environment file on a clean first run.
if not exist ".env" (
  if exist ".env.example" (
    copy /y ".env.example" ".env" >nul
    echo [OK] Created .env from .env.example.
  ) else (
    echo [X] Neither .env nor .env.example was found.
    pause
    exit /b 1
  )
)

REM 4) Initialize only a missing database. Never overwrite or reseed an existing one.
if not exist "db.sqlite3" (
  echo [..] Creating the local database for first use...
  "%VENV_PYTHON%" manage.py migrate --noinput
  if errorlevel 1 (
    echo.
    echo [X] Database initialization failed.
    pause
    exit /b 1
  )
  echo [OK] Local database created.
)

REM 5) Validate the Django project before opening the browser.
echo [..] Checking the application...
"%VENV_PYTHON%" manage.py check
if errorlevel 1 (
  echo.
  echo [X] Construction ERP did not pass its startup check.
  echo     Review the error above, then run this file again.
  pause
  exit /b 1
)

REM Avoid starting a second server on the same port.
netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  echo.
  echo [!] Port 8000 is already in use. Opening the existing address instead.
  start "" "%APP_URL%"
  echo.
  pause
  exit /b 0
)

echo.
echo [^>] Starting Construction ERP at %APP_URL%
echo.
echo     Keep this window open while using the application.
echo     To stop the server, press Ctrl+C or close this window.
echo.

REM Give Django a moment to start, then open the default browser.
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process '%APP_URL%'"

"%VENV_PYTHON%" manage.py runserver 127.0.0.1:8000

echo.
echo Construction ERP has stopped.
pause
endlocal
