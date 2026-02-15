@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal

echo ========================================
echo Fetch 1R only (KIRYU 2026-02-14 1R)
echo ========================================
echo.

set VENV_PATH=%~dp0..\venv
set PY_EXE=%VENV_PATH%\Scripts\python.exe
if exist "%PY_EXE%" (
    echo Using venv: %VENV_PATH%
) else (
    set PY_EXE=python
    echo Using system Python.
)

echo.
echo Output: kyotei_predictor/data/raw
echo.

"%PY_EXE%" -m kyotei_predictor.tools.batch.batch_fetch_all_venues ^
  --start-date 2026-02-14 ^
  --end-date 2026-02-14 ^
  --stadiums KIRYU ^
  --races 1 ^
  --output-data-dir "kyotei_predictor/data/raw"

if errorlevel 1 (
    echo.
    echo Fetch failed.
    pause
    exit /b 1
)

echo.
echo Done. Check: kyotei_predictor\data\raw\2026-02\20260214\KIRYU\
pause
