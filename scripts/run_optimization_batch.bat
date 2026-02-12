@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Kyotei Prediction Optimization Batch
echo ========================================
echo.

set VENV_PATH=venv
set PYTHON_SCRIPT=kyotei_predictor/tools/optimization/optimize_graduated_reward.py
set LOG_DIR=logs
set OPTUNA_DIRS=optuna_logs,optuna_models,optuna_results,optuna_studies,optuna_tensorboard

if not exist %LOG_DIR% mkdir %LOG_DIR%
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a%%b%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a%%b
set TIMESTAMP=%DATE%_%TIME%
set LOG_FILE=%LOG_DIR%\optimization_%TIMESTAMP%.log

echo Start: %date% %time%
echo Log: %LOG_FILE%
echo.

if not exist "%VENV_PATH%\Scripts\Activate.bat" (
    echo Creating venv: %VENV_PATH%
    python -m venv %VENV_PATH%
)
call "%VENV_PATH%\Scripts\Activate.bat"

python -c "import optuna, stable_baselines3" 2>nul
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
)

echo Starting optimization...
set START_TIME=%time%
echo Start: %START_TIME% >> %LOG_FILE%
python %PYTHON_SCRIPT% --medium-mode --n-trials 20 --year-month 2024-02 >> %LOG_FILE% 2>&1
set END_TIME=%time%
echo End: %END_TIME% >> %LOG_FILE%

if errorlevel 1 (
    echo Optimization failed. Check log: %LOG_FILE%
) else (
    echo Optimization completed. Results: optuna_results/
)
echo Log: %LOG_FILE%
call :cleanup_old_files
pause
exit /b 0

:cleanup_old_files
echo Cleaning old files...
for %%d in (%OPTUNA_DIRS%) do (
    if exist %%d (
        forfiles /p %%d /s /m *.* /d -7 /c "cmd /c del @path" 2>nul
    )
)
if exist %LOG_DIR% (
    forfiles /p %LOG_DIR% /s /m *.log /d -30 /c "cmd /c del @path" 2>nul
)
goto :eof
