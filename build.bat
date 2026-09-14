@echo off
setlocal
cd /d "%~dp0"

set "VENV=.build-venv"
set "PYTHON=%VENV%\Scripts\python.exe"

if not exist "%PYTHON%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.11 -m venv "%VENV%"
    ) else (
        python -m venv "%VENV%"
    )
    if errorlevel 1 goto :fail
)

"%PYTHON%" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :fail

set "PYTHONPATH=%CD%\src"
"%PYTHON%" -m unittest discover -s tests
if errorlevel 1 goto :fail

"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name KadokaTetrisAI ^
    --paths src ^
    src\tetris\main.py
if errorlevel 1 goto :fail

"%PYTHON%" tools\distribution\smoke_test.py dist\KadokaTetrisAI
if errorlevel 1 goto :fail

echo [build] dist\KadokaTetrisAI is ready for packaging.
exit /b 0

:fail
echo [build] FAILED
exit /b 1
