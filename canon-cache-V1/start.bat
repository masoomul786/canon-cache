@echo off
title CanonCache Launcher
echo.
echo  ============================================
echo   CanonCache - KV-Cache Research Tool
echo  ============================================
echo.

:: Check Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Show Python version
echo  Python: 
python --version

:: Install/check dependencies
echo.
echo  Checking dependencies...
pip install -r requirements.txt --quiet

:: Launch app
echo.
echo  Launching CanonCache...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Application exited with an error.
    pause
)
