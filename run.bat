@echo off
REM ===========================================================================
REM  IncidentIQ - one-click launcher for Windows.
REM  Double-click this file. It creates a virtual environment on first run,
REM  installs the dependencies, starts the server and opens a browser.
REM ===========================================================================

setlocal
cd /d "%~dp0"

echo.
echo  IncidentIQ - starting up
echo  ------------------------

REM --- locate Python ---------------------------------------------------------
where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo.
        echo  Python 3.10 or newer was not found on this machine.
        echo  Install it from https://www.python.org/downloads/ and tick
        echo  "Add Python to PATH" during setup, then run this file again.
        echo.
        pause
        exit /b 1
    )
)

REM --- virtual environment ---------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo  Creating a virtual environment ^(first run only^)...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo  Could not create the virtual environment.
        pause
        exit /b 1
    )
    set "FRESH=1"
)

set "VENV_PY=.venv\Scripts\python.exe"

REM --- dependencies ----------------------------------------------------------
if defined FRESH (
    echo  Installing dependencies ^(this takes a minute the first time^)...
    "%VENV_PY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
    "%VENV_PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
    if errorlevel 1 (
        echo  Dependency installation failed. Check the network connection.
        pause
        exit /b 1
    )
) else (
    "%VENV_PY%" -c "import fastapi, uvicorn" >nul 2>nul
    if errorlevel 1 (
        echo  Installing missing dependencies...
        "%VENV_PY%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
    )
)

REM --- go --------------------------------------------------------------------
"%VENV_PY%" run.py

echo.
echo  IncidentIQ has stopped.
pause
endlocal
