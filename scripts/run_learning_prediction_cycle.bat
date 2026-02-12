@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal

echo ========================================
echo Learning -^> Prediction Cycle (test_raw)
echo ========================================
echo.

set VENV_PATH=venv
if exist "%VENV_PATH%\Scripts\Activate.bat" (
    echo Activating venv: %VENV_PATH%
    call "%VENV_PATH%\Scripts\Activate.bat"
) else (
    echo No venv found. Using system Python.
)

echo.
echo [1/2] Learning (minimal, 1 trial, test_raw)...
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir kyotei_predictor/data/test_raw --year-month 2024-05 --minimal --n-trials 1
if errorlevel 1 (
    echo Learning failed. Exiting.
    pause
    exit /b 1
)

echo.
echo [2/2] Prediction (2024-05-01, test_raw)...
python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --data-dir kyotei_predictor/data/test_raw
if errorlevel 1 (
    echo Prediction failed. Exiting.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Cycle completed. Check outputs\predictions_2024-05-01.json
echo ========================================
pause
