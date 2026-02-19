@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal

echo ========================================
echo 過去5年分のデータ取得
echo ========================================
echo.
echo 期間: 2021-01-01 〜 2026-02-14（全会場・全レース）
echo 初回または欠けている分だけ取得します（既存はスキップ）。
echo 全て取り直す場合はこの .bat 内で OVERWRITE=1 に変更してください。
echo.
echo 注意: 5年分は件数が多く、完了まで数時間〜終日かかる場合があります。
echo       夜間や休日に実行することを推奨します。
echo.

REM 過去5年: 2021-01-01 〜 2026-02-14
set START_DATE=2021-01-01
set END_DATE=2026-02-14
set STADIUMS=ALL
set OUT_DIR=kyotei_predictor/data/raw
REM 0=欠けている分だけ取得 / 1=既存も上書きして取り直し
set OVERWRITE=0

set VENV_PATH=venv
if exist "%VENV_PATH%\Scripts\Activate.bat" (
    call "%VENV_PATH%\Scripts\Activate.bat"
)

if "%OVERWRITE%"=="1" (
  set OVERWRITE_FLAG=--overwrite
) else (
  set OVERWRITE_FLAG=
)

echo 開始: %START_DATE% 〜 %END_DATE% 会場=%STADIUMS% 上書き=%OVERWRITE%
echo.

python -m kyotei_predictor.tools.batch.batch_fetch_all_venues ^
  --start-date %START_DATE% ^
  --end-date %END_DATE% ^
  --stadiums %STADIUMS% ^
  --output-data-dir "%OUT_DIR%" ^
  --rate-limit 1 ^
  --schedule-workers 3 ^
  --race-workers 3 %OVERWRITE_FLAG%

if errorlevel 1 (
    echo 取得に失敗しました。
    pause
    exit /b 1
)
echo 完了。
pause
