@echo off
chcp 65001 >nul
REM Production optimization with continuous learning system
REM Full production execution with cleanup after completion

echo ========================================
echo Production Optimization with Continuous Learning
echo ========================================
echo.

REM Check if data month is provided as argument
set DATA_MONTH=%1
if "%DATA_MONTH%"=="" (
    echo Usage: run_optimization_production_continuous.bat [DATA_MONTH]
    echo Example: run_optimization_production_continuous.bat 2024-01
    echo Example: run_optimization_production_continuous.bat 2024-02
    echo.
    echo Available data months:
    if exist "kyotei_predictor\data\raw" (
        for /d %%i in ("kyotei_predictor\data\raw\*") do (
            echo - %%~ni
        )
    ) else (
        echo No data directories found
    )
    echo.
    pause
    exit /b 1
)

echo Data month: %DATA_MONTH%
echo.

REM 1. Virtual environment activation
echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment activation failed
    exit /b 1
)
echo OK: Virtual environment activated

REM 2. Dependency check
echo.
echo [2/5] Checking dependencies...
python -c "import numpy, torch, stable_baselines3, optuna; print('OK: All dependencies available')"
if errorlevel 1 (
    echo ERROR: Dependency check failed
    exit /b 1
)

REM 3. Data check
echo.
echo [3/5] Checking data...
if not exist "kyotei_predictor\data\raw\%DATA_MONTH%" (
    echo ERROR: %DATA_MONTH% data not found
    echo.
    echo Available data directories:
    if exist "kyotei_predictor\data\raw" (
        for /d %%i in ("kyotei_predictor\data\raw\*") do (
            echo - %%~ni
        )
    ) else (
        echo No data directories found
    )
    echo.
    pause
    exit /b 1
)
echo OK: %DATA_MONTH% data confirmed

REM 4. Production optimization execution with continuous learning
echo.
echo [4/5] Starting production optimization with continuous learning...
echo Data month: %DATA_MONTH%
echo Mode: Production with Continuous Learning
echo Trials: 50
echo Timesteps: 100000
echo Eval episodes: 200
echo.

REM Production optimization execution with continuous learning system
python kyotei_predictor\tools\optimization\integrated_continuous_optimizer.py --mode continuous --n_trials 50 --data_dir kyotei_predictor/data/raw/%DATA_MONTH%

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

REM 5. Cleanup execution
echo.
echo [5/5] Running cleanup...
echo.

REM Run cleanup script
python -m kyotei_predictor.tools.maintenance.auto_cleanup

if errorlevel 1 (
    echo.
    echo WARNING: Cleanup failed, but optimization completed successfully
) else (
    echo.
    echo OK: Cleanup completed
)

echo.
echo ========================================
echo ALL PROCESSES COMPLETED
echo ========================================
echo.
echo Results saved to:
echo - ./optuna_models/graduated_reward_best_%DATA_MONTH%/
echo - ./optuna_studies/
echo - ./optuna_results/
echo - ./final_results/ (important results)
echo - ./results/ (detailed results)
echo.
echo Continuous Learning System Results:
echo - Training history: ./optuna_results/training_history.json
echo - Curriculum config: ./optuna_results/curriculum_config.json
echo - Training progress: ./optuna_results/training_progress.png
echo.
echo Cleanup completed for:
echo - Old log files
echo - Old model checkpoints
echo - Temporary files
echo.
pause 