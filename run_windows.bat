@echo off
REM SlipSurfaceIQ Settle - Windows: creates/updates the virtual environment and starts the app.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    .venv\Scripts\python.exe -m pip install --upgrade pip
)
REM Reinstall packages if requirements.txt changed (new release)
fc /b requirements.txt .venv\requirements.stamp >nul 2>&1
if errorlevel 1 (
    echo Installing / updating required packages...
    .venv\Scripts\python.exe -m pip install -r requirements.txt && copy /y requirements.txt .venv\requirements.stamp >nul
)
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); import slipsurface.settle as s, os; print('SlipSurfaceIQ Settle', s.__version__, '-', os.path.dirname(s.__file__))"
.venv\Scripts\python.exe main.py %*
if errorlevel 1 pause
