@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Kyotei Prediction Optimization Batch
echo ========================================
echo.

:: Load configuration file
set CONFIG_FILE=optimization_config.ini
if not exist %CONFIG_FILE% (
    echo Warning: Config file not found: %CONFIG_FILE%
    echo Using default settings...
    goto :default_config
)

:: Read values from config file
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
:: Default settings
set MODE=fast
set TRIALS=20
set YEAR_MONTH=2024-01
set VENV_PATH=venv
set LOG_DIR=logs
set CLEANUP_DAYS=7

:check_config
:: Display current settings
echo Current Settings:
echo   Mode: %MODE%
echo   Trials: %TRIALS%
echo   Year-Month: %YEAR_MONTH%
echo   Virtual Environment: %VENV_PATH%
echo   Log Directory: %LOG_DIR%
echo   Cleanup Days: %CLEANUP_DAYS% days
echo.

:: Auto-execute without user input
echo Auto-executing optimization with current settings...
echo.

:: Main execution
call :main_execution
goto :eof

:main_execution
:: Create log directory
if not exist %LOG_DIR% mkdir %LOG_DIR%

:: Get current timestamp with high precision
echo Getting high precision timestamp...
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a%%b%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a%%b

:: Get high precision timestamp using PowerShell
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set HIGH_PRECISION_TIMESTAMP=%%a
set TIMESTAMP=%HIGH_PRECISION_TIMESTAMP%
set LOG_FILE=%LOG_DIR%\optimization_%TIMESTAMP%.log

echo Start time: %date% %time%
echo Log file: %LOG_FILE%
echo.

:: Check/create virtual environment
if not exist "%VENV_PATH%\Scripts\Activate.bat" (
    echo Virtual environment not found: %VENV_PATH%
    echo Creating virtual environment...
    python -m venv %VENV_PATH%
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call "%VENV_PATH%\Scripts\Activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated

:: Check dependencies
echo Checking dependencies...
python -c "import stable_baselines3, optuna" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install packages
        pause
        exit /b 1
    )
)

:: Start optimization
echo Starting optimization...
echo Settings: %MODE% mode, %TRIALS% trials, %YEAR_MONTH% data

:: Build command
set PYTHON_SCRIPT=kyotei_predictor\tools\optimization\optimize_graduated_reward.py
set CMD_ARGS=--n-trials %TRIALS%

:: Add mode-specific arguments
if "%MODE%"=="fast" (
    set CMD_ARGS=%CMD_ARGS% --fast-mode
) else if "%MODE%"=="medium" (
    set CMD_ARGS=%CMD_ARGS% --medium-mode
) else if "%MODE%"=="normal" (
    :: Normal mode - no additional flags
) else (
    echo Warning: Unknown mode '%MODE%', using fast mode as default
    set CMD_ARGS=%CMD_ARGS% --fast-mode
)

if not "%YEAR_MONTH%"=="" (
    set CMD_ARGS=%CMD_ARGS% --year-month %YEAR_MONTH%
)

echo Command: python %PYTHON_SCRIPT% %CMD_ARGS%

:: Execute optimization
:: Get start time with better precision
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set START_TIME=%%a:%%b
echo Start time: %START_TIME% >> %LOG_FILE%
echo [BATCH] Optimization started at: %START_TIME% >> %LOG_FILE%

:: Execute the optimization script
python %PYTHON_SCRIPT% %CMD_ARGS% >> %LOG_FILE% 2>&1
set OPTIMIZATION_EXIT_CODE=%errorlevel%

:: Get end time with better precision
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set END_TIME=%%a:%%b
echo End time: %END_TIME% >> %LOG_FILE%
echo [BATCH] Optimization ended at: %END_TIME% >> %LOG_FILE%

:: Calculate execution time
call :calculate_execution_time %START_TIME% %END_TIME%
echo [BATCH] Total execution time: %EXECUTION_TIME% >> %LOG_FILE%

:: Cleanup old files
call :cleanup_old_files

echo.
echo ========================================
echo Optimization completed
echo ========================================
echo Start time: %START_TIME%
echo End time: %END_TIME%
echo Total execution time: %EXECUTION_TIME%
echo Log file: %LOG_FILE%
echo Exit code: %OPTIMIZATION_EXIT_CODE%
echo.
echo [BATCH] Summary:
echo   - Mode: %MODE%
echo   - Trials: %TRIALS%
echo   - Year-Month: %YEAR_MONTH%
echo   - Execution time: %EXECUTION_TIME%
echo   - Log file: %LOG_FILE%
echo.
if %OPTIMIZATION_EXIT_CODE% equ 0 (
    echo [BATCH] Optimization completed successfully!
) else (
    echo [BATCH] Optimization completed with exit code: %OPTIMIZATION_EXIT_CODE%
)
echo.
goto :eof

:calculate_execution_time
set START_H=%1
set END_H=%2
for /f "tokens=1-3 delims=:." %%a in ("%START_H%") do (
    set START_HOUR=%%a
    set START_MIN=%%b
    set START_SEC=%%c
)
for /f "tokens=1-3 delims=:." %%a in ("%END_H%") do (
    set END_HOUR=%%a
    set END_MIN=%%b
    set END_SEC=%%c
)
if "%START_HOUR%"=="" set START_HOUR=0
if "%START_MIN%"=="" set START_MIN=0
if "%START_SEC%"=="" set START_SEC=0
if "%END_HOUR%"=="" set END_HOUR=0
if "%END_MIN%"=="" set END_MIN=0
if "%END_SEC%"=="" set END_SEC=0
set /a START_TOTAL_SECS=(%START_HOUR%*3600)+(%START_MIN%*60)+%START_SEC% 2>nul
set /a END_TOTAL_SECS=(%END_HOUR%*3600)+(%END_MIN%*60)+%END_SEC% 2>nul
set /a DIFF_SECS=%END_TOTAL_SECS%-%START_TOTAL_SECS% 2>nul
if %DIFF_SECS% lss 0 (
    set /a DIFF_SECS=%DIFF_SECS%+86400 2>nul
)
set /a HOURS=%DIFF_SECS%/3600 2>nul
set /a MINUTES=(%DIFF_SECS%%%3600)/60 2>nul
set /a SECONDS=%DIFF_SECS%%%60 2>nul
if %HOURS% lss 10 set HOURS=0%HOURS%
if %MINUTES% lss 10 set MINUTES=0%MINUTES%
if %SECONDS% lss 10 set SECONDS=0%SECONDS%
set EXECUTION_TIME=%HOURS%:%MINUTES%:%SECONDS%
goto :eof

:cleanup_old_files
echo.
echo Cleaning up old files...
echo Cleanup target: %CLEANUP_DAYS% days old
set OPTUNA_DIRS=optuna_logs optuna_models optuna_results optuna_studies optuna_tensorboard
set COUNT=0
for %%d in (%OPTUNA_DIRS%) do (
    if exist %%d (
        echo Cleaning %%d...
        forfiles /p %%d /s /m *.* /d -%CLEANUP_DAYS% /c "cmd /c del @path && set /a COUNT+=1" 2>nul
        if !COUNT! gtr 0 (
            echo Removed !COUNT! files from %%d
        ) else (
            echo No old files found in %%d
        )
        set COUNT=0
    )
)
set LOG_COUNT=0
if exist %LOG_DIR% (
    echo Cleaning old log files...
    forfiles /p %LOG_DIR% /s /m *.log /d -30 /c "cmd /c del @path && set /a LOG_COUNT+=1" 2>nul
    if !LOG_COUNT! gtr 0 (
        echo Removed !LOG_COUNT! old log files
    ) else (
        echo No old log files found
    )
)
for %%d in (%OPTUNA_DIRS%) do (
    if exist %%d (
        rmdir /s /q %%d 2>nul
        if exist %%d (
            echo Note: %%d still contains files
        ) else (
            echo Removed empty directory: %%d
        )
    )
)
echo Cleanup completed
echo.
goto :eof
