@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Cleanup old files
echo ========================================
echo.

set ROOT_OPTUNA_DIRS=optuna_studies_backup_20250806_174103
set KYOTEI_OPTUNA_DIRS=kyotei_predictor\optuna_logs kyotei_predictor\optuna_models kyotei_predictor\optuna_results kyotei_predictor\optuna_studies kyotei_predictor\optuna_tensorboard kyotei_predictor\optuna_studies_backup
set KYOTEI_TENSORBOARD_DIRS=kyotei_predictor\simple_test_tensorboard kyotei_predictor\ppo_tensorboard
set LOG_DIR=logs
set CLEANUP_DAYS=7

echo Cleaning files older than %CLEANUP_DAYS% days...
echo.

for %%d in (%ROOT_OPTUNA_DIRS%) do (
    if exist %%d (
        echo Cleaning %%d...
        forfiles /p %%d /s /m *.* /d -%CLEANUP_DAYS% /c "cmd /c del @path" 2>nul
        echo Done %%d
    )
)

for %%d in (%KYOTEI_OPTUNA_DIRS%) do (
    if exist %%d (
        echo Cleaning %%d...
        forfiles /p %%d /s /m *.* /d -%CLEANUP_DAYS% /c "cmd /c del @path" 2>nul
        echo Done %%d
    )
)

for %%d in (%KYOTEI_TENSORBOARD_DIRS%) do (
    if exist %%d (
        echo Cleaning %%d...
        forfiles /p %%d /s /m *.* /d -%CLEANUP_DAYS% /c "cmd /c del @path" 2>nul
        echo Done %%d
    )
)

if exist %LOG_DIR% (
    echo Cleaning old logs in %LOG_DIR%...
    forfiles /p %LOG_DIR% /s /m *.log /d -30 /c "cmd /c del @path" 2>nul
)
if exist kyotei_predictor\logs (
    echo Cleaning old logs in kyotei_predictor\logs...
    forfiles /p kyotei_predictor\logs /s /m *.log /d -30 /c "cmd /c del @path" 2>nul
)

for %%d in (%ROOT_OPTUNA_DIRS%) do (
    if exist %%d (
        rmdir /s /q %%d 2>nul
    )
)
for %%d in (%KYOTEI_OPTUNA_DIRS% %KYOTEI_TENSORBOARD_DIRS%) do (
    if exist %%d (
        rmdir /s /q %%d 2>nul
    )
)

echo.
echo Cleanup completed.
pause
