@echo off
echo ========================================
echo Cleanup Script
echo ========================================

echo [1/4] Cleaning temporary files...
if exist "*.log" del /q "*.log"
if exist "auto_cleanup.log" del /q "auto_cleanup.log"
if exist "check_*.py" del /q "check_*.py"
if exist "test_*.py" del /q "test_*.py"
if exist "simple_*.py" del /q "simple_*.py"
if exist "run_test*.bat" del /q "run_test*.bat"

echo [2/4] Cleaning temporary directories...
if exist "temp" rmdir /s /q "temp"
if exist "tmp" rmdir /s /q "tmp"

echo [3/4] Cleaning optimization temporary files...
if exist "kyotei_predictor\logs\*.log" del /q "kyotei_predictor\logs\*.log"

echo [4/4] Cleanup completed!
echo.
echo Cleanup finished successfully. 