@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal

echo ========================================
echo 期間を指定してデータ再取得
echo ========================================
echo.
echo 下記の期間・会場で再取得します。
echo 変更する場合はこの .bat を編集してください。
echo.

REM ここを編集して再取得したい期間・会場に変更
set START_DATE=2026-02-01
set END_DATE=2026-02-14
set STADIUMS=ALL
set OUT_DIR=kyotei_predictor/data/raw
REM 過去分を取り直す（既存ファイルを上書き）する場合は OVERWRITE=1 に
set OVERWRITE=1

set VENV_PATH=venv
if exist "%VENV_PATH%\Scripts\Activate.bat" (
    call "%VENV_PATH%\Scripts\Activate.bat"
)

if "%OVERWRITE%"=="1" (
  set OVERWRITE_FLAG=--overwrite
) else (
  set OVERWRITE_FLAG=
)

echo 期間: %START_DATE% 〜 %END_DATE%
echo 会場: %STADIUMS%
echo 出力: %OUT_DIR%
echo 上書き: %OVERWRITE% (1=既存も再取得)
echo.

python -m kyotei_predictor.tools.batch.batch_fetch_all_venues ^
  --start-date %START_DATE% ^
  --end-date %END_DATE% ^
  --stadiums %STADIUMS% ^
  --output-data-dir "%OUT_DIR%" %OVERWRITE_FLAG%

if errorlevel 1 (
    echo 再取得に失敗しました。
    pause
    exit /b 1
)
echo 完了。
pause
