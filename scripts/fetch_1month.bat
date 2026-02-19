@echo off
cd /d "%~dp0\.."
chcp 65001 >nul
setlocal

echo ========================================
echo 過去1か月分のデータ取得（2026年1月）
echo ========================================
echo.
echo 期間: 2026-01-01 〜 2026-01-31
echo 会場: 全会場（24会場）
echo 出力: kyotei_predictor/data/raw
echo 既存ファイル: スキップ（欠けている分のみ取得）
echo.

set START_DATE=2026-01-01
set END_DATE=2026-01-31
set STADIUMS=ALL
set OUT_DIR=kyotei_predictor/data/raw
REM 既存ファイルはスキップ（初回取得のため --overwrite なし）
set OVERWRITE=0

set VENV_PATH=venv
if exist "%VENV_PATH%\Scripts\Activate.bat" (
    call "%VENV_PATH%\Scripts\Activate.bat"
)

python -m kyotei_predictor.tools.batch.batch_fetch_all_venues ^
  --start-date %START_DATE% ^
  --end-date %END_DATE% ^
  --stadiums %STADIUMS% ^
  --output-data-dir "%OUT_DIR%"

if errorlevel 1 (
    echo 取得に失敗しました。
    pause
    exit /b 1
)
echo 完了。
pause
