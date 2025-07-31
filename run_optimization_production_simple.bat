@echo off
chcp 65001 >nul
REM Production optimization execution
REM Simple batch file for production mode

echo ========================================
echo Production Optimization Execution
echo ========================================
echo.

REM 1. Virtual environment activation
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment activation failed
    exit /b 1
)
echo OK: Virtual environment activated

REM 2. Dependency check
echo.
echo [2/4] Checking dependencies...
python -c "import numpy, torch, stable_baselines3, optuna; print('OK: All dependencies available')"
if errorlevel 1 (
    echo ERROR: Dependency check failed
    exit /b 1
)

REM 3. Data check
echo.
echo [3/4] Checking data...
if not exist "kyotei_predictor\data\raw\2024-01" (
    echo ERROR: 2024-01 data not found
    exit /b 1
)
echo OK: 2024-01 data confirmed

REM 4. Production optimization execution
echo.
echo [4/4] Starting production optimization...
echo Data month: 2024-01
echo Mode: Production
echo Trials: 30
echo.

REM Production optimization execution
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --n-trials 30

if errorlevel 1 (
    echo.
    echo ERROR: Production optimization failed
    exit /b 1
)

echo.
echo ========================================
echo OK: Production optimization completed
echo ========================================
echo.
echo Results saved to:
echo - ./optuna_models/graduated_reward_best_202401/
echo - ./optuna_studies/
echo. 