@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
REM Interactive optimization execution batch file
REM Setup + user selection for optimization execution

echo ========================================
echo Boat Race Prediction Model Optimization (Interactive)
echo ========================================
echo.

REM 1. Virtual environment activation
echo [1/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment activation failed
    echo If virtual environment does not exist, run:
    echo python -m venv venv
    pause
    exit /b 1
)
echo OK: Virtual environment activated

REM 2. Dependency check
echo.
echo [2/6] Checking dependencies...
python -c "import numpy, torch, stable_baselines3, optuna; print('OK: Dependencies confirmed')"
if errorlevel 1 (
    echo ERROR: Dependency check failed
    echo Install dependencies with:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM 3. Data month selection
echo.
echo [3/6] Selecting data month...
echo.
echo Available data months:
if exist "kyotei_predictor\data\raw" (
    set /a count=1
    for /d %%i in ("kyotei_predictor\data\raw\*") do (
        echo !count!. %%~ni
        set "month_!count!=%%~ni"
        set /a count+=1
    )
    set /a total_months=!count!-1
) else (
    echo No data directories found
    pause
    exit /b 1
)

echo.
echo Select optimization target data month:
echo 1-%total_months%. Available data months
echo 0. Manual input
echo.
set /p month_choice="Choice (0-%total_months%): "

if "%month_choice%"=="0" (
    echo.
    echo Enter data month (e.g., 2024-01):
    set /p DATA_MONTH="Data month: "
    set MONTH_NAME=%DATA_MONTH%
) else if "%month_choice%" geq "1" if "%month_choice%" leq "%total_months%" (
    call set DATA_MONTH=%%month_%month_choice%%%
    set MONTH_NAME=%DATA_MONTH%
) else (
    echo Invalid choice. Please select 0-%total_months%.
    pause
    exit /b 1
)

REM 4. Data verification
echo.
echo [4/6] Verifying data...
if not exist "kyotei_predictor\data\raw\%DATA_MONTH%" (
    echo ERROR: %MONTH_NAME% data not found
    echo Check data directory: kyotei_predictor\data\raw\%DATA_MONTH%
    pause
    exit /b 1
)
echo OK: %MONTH_NAME% data confirmed

REM 5. Execution mode selection
echo.
echo [5/6] Selecting execution mode...
echo.
echo Select execution mode:
echo 1. Test mode (short time, 3 trials)
echo 2. Production mode (long time, 50 trials)
echo.
set /p choice="Choice (1-2): "

if "%choice%"=="1" (
    echo Running in test mode...
    set TRIALS=3
    set TEST_MODE=--test-mode
    set MODE_NAME=Test mode
) else if "%choice%"=="2" (
    echo Running in production mode...
    set TRIALS=50
    set TEST_MODE=
    set MODE_NAME=Production mode
) else (
    echo Invalid choice. Please select 1 or 2.
    pause
    exit /b 1
)

REM 6. Optimization execution
echo.
echo [6/6] Executing optimization...
echo Starting %MODE_NAME% optimization for %MONTH_NAME% data (%TRIALS% trials)
echo.

REM Optimization execution
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month %DATA_MONTH% --n-trials %TRIALS% %TEST_MODE%

if errorlevel 1 (
    echo.
    echo ERROR: Optimization execution failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo OK: Optimization completed successfully
echo ========================================
echo.
echo Execution mode: %MODE_NAME%
echo Target data: %MONTH_NAME%
echo Trial count: %TRIALS%
echo.
echo Result files:
echo - optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json
echo - optuna_studies/graduated_reward_optimization_YYYYMMDD_HHMMSS.db
echo.
pause 