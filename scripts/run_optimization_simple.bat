@echo off
cd /d "%~dp0\.."
chcp 65001 >nul

echo ========================================
echo Kyotei Prediction Optimization (Simple)
echo ========================================
echo.

set CONFIG_FILE=optimization_config.ini
if not exist %CONFIG_FILE% (
    echo Warning: Config file not found: %CONFIG_FILE%
    goto :default_config
)
for /f "tokens=1,2 delims==" %%a in (%CONFIG_FILE%) do (
    if "%%a"=="MODE" set MODE=%%b
    if "%%a"=="TRIALS" set TRIALS=%%b
    if "%%a"=="YEAR_MONTH" set YEAR_MONTH=%%b
    if "%%a"=="VENV_PATH" set VENV_PATH=%%b
    if "%%a"=="LOG_DIR" set LOG_DIR=%%b
    if "%%a"=="CLEANUP_DAYS" set CLEANUP_DAYS=%%b
)
goto :check_config

:default_config
set MODE=fast
set TRIALS=20
set YEAR_MONTH=2024-01
set VENV_PATH=venv
set LOG_DIR=logs
set CLEANUP_DAYS=7

:check_config
echo Mode: %MODE%  Trials: %TRIALS%  Year-Month: %YEAR_MONTH%
echo.

if not exist %LOG_DIR% mkdir %LOG_DIR%
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set TIMESTAMP=%%a
set LOG_FILE=%LOG_DIR%\optimization_%TIMESTAMP%.log

if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo Virtual environment not found: %VENV_PATH%
    pause
    exit /b 1
)

set PYTHON_SCRIPT=kyotei_predictor\tools\optimization\optimize_graduated_reward.py
set CMD_ARGS=--n-trials %TRIALS%
if "%MODE%"=="fast" set CMD_ARGS=%CMD_ARGS% --fast-mode
if "%MODE%"=="medium" set CMD_ARGS=%CMD_ARGS% --medium-mode
if not "%YEAR_MONTH%"=="" set CMD_ARGS=%CMD_ARGS% --year-month %YEAR_MONTH%

echo Starting optimization...
echo [BATCH] Start: %time% >> %LOG_FILE%
"%VENV_PATH%\Scripts\python.exe" %PYTHON_SCRIPT% %CMD_ARGS% >> %LOG_FILE% 2>&1
set OPTIMIZATION_EXIT_CODE=%errorlevel%
echo [BATCH] End: %time% >> %LOG_FILE%

echo.
echo Optimization completed. Exit code: %OPTIMIZATION_EXIT_CODE%
echo Log: %LOG_FILE%
pause
