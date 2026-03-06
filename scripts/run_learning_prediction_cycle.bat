@echo off
REM Learning->Prediction->Verification. OS-independent single commands: see docs\OS_PORTABILITY_STRATEGY.md
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
echo [1/3] Learning (minimal, 1 trial, test_raw)...
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir kyotei_predictor/data/test_raw --year-month 2024-05 --minimal --n-trials 1
if errorlevel 1 (
    echo Learning failed. Exiting.
    pause
    exit /b 1
)

echo.
echo [2/3] Prediction (2024-05-01, test_raw)...
python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --data-dir kyotei_predictor/data/test_raw
if errorlevel 1 (
    echo Prediction failed. Exiting.
    pause
    exit /b 1
)

echo.
echo [3/3] Verification (predictions vs actuals)...
if exist "outputs\predictions_2024-05-01.json" (
    python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --data-dir kyotei_predictor/data/test_raw
) else (
    echo Skip verification: outputs\predictions_2024-05-01.json not found.
)

echo.
echo ========================================
echo Cycle completed. Check outputs\predictions_2024-05-01.json and logs\verification_*.txt
echo ========================================
pause
