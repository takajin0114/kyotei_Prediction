@echo off
chcp 65001 >nul
REM Production optimization with continuous learning system and evaluation
REM Full production execution with evaluation and cleanup after completion

echo ========================================
echo Production Optimization with Continuous Learning and Evaluation
echo ========================================
echo.

REM Check if data month is provided as argument
set DATA_MONTH=%1
if "%DATA_MONTH%"=="" (
    echo Usage: run_optimization_production_continuous_with_evaluation.bat [DATA_MONTH]
    echo Example: run_optimization_production_continuous_with_evaluation.bat 2024-01
    echo Example: run_optimization_production_continuous_with_evaluation.bat 2024-02
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
echo [1/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment activation failed
    exit /b 1
)
echo OK: Virtual environment activated

REM 2. Dependency check
echo.
echo [2/6] Checking dependencies...
python -c "import numpy, torch, stable_baselines3, optuna; print('OK: All dependencies available')"
if errorlevel 1 (
    echo ERROR: Dependency check failed
    exit /b 1
)

REM 3. Data check
echo.
echo [3/6] Checking data...
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
echo [4/6] Starting production optimization with continuous learning...
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

REM 5. Model evaluation
echo.
echo [5/6] Starting model evaluation...
echo.

REM Find the best model from optimization results
echo Finding best model for evaluation...
for /f "tokens=*" %%i in ('dir /b /od "optuna_models\trial_*" 2^>nul') do (
    set BEST_TRIAL=%%i
)

if "%BEST_TRIAL%"=="" (
    echo ERROR: No trial models found for evaluation
    echo Skipping evaluation...
    goto :cleanup
)

echo Found best trial: %BEST_TRIAL%

REM Find the best checkpoint in the trial
for /f "tokens=*" %%i in ('dir /b /od "optuna_models\%BEST_TRIAL%\checkpoint_*_steps.zip" 2^>nul') do (
    set BEST_MODEL=%%i
)

if "%BEST_MODEL%"=="" (
    echo ERROR: No checkpoint models found in %BEST_TRIAL%
    echo Skipping evaluation...
    goto :cleanup
)

echo Found best model: %BEST_MODEL%

REM Run evaluation
echo.
echo Running model evaluation...
echo Model: optuna_models\%BEST_TRIAL%\%BEST_MODEL%
echo Data: kyotei_predictor\data\raw\%DATA_MONTH%
echo Episodes: 1000
echo.

python kyotei_predictor\tools\evaluation\evaluate_graduated_reward_model.py --model_path "optuna_models\%BEST_TRIAL%\%BEST_MODEL%" --n_eval_episodes 1000 --data_dir "kyotei_predictor/data/raw/%DATA_MONTH%"

if errorlevel 1 (
    echo.
    echo WARNING: Model evaluation failed, but optimization completed successfully
) else (
    echo.
    echo OK: Model evaluation completed
)

REM 6. Cleanup execution
:cleanup
echo.
echo [6/6] Running cleanup...
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
echo - ./outputs/ (evaluation results)
echo.
echo Continuous Learning System Results:
echo - Training history: ./optuna_results/training_history.json
echo - Curriculum config: ./optuna_results/curriculum_config.json
echo - Training progress: ./optuna_results/training_progress.png
echo.
echo Evaluation Results:
echo - Model evaluation: ./outputs/graduated_reward_evaluation_*.json
echo - Evaluation plots: ./outputs/evaluation_plots_*.png
echo.
echo Cleanup completed for:
echo - Old log files
echo - Old model checkpoints
echo - Temporary files
echo.
pause 