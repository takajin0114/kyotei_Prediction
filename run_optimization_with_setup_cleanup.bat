@echo off
REM 自動クリーンアップ付き最適化実行バッチファイル
REM 前段準備 + 最適化実行 + 自動クリーンアップ

echo ========================================
echo 競艇予測モデル最適化実行バッチ（自動クリーンアップ付き）
echo ========================================
echo.

REM 1. 仮想環境の有効化
echo [1/6] 仮想環境の有効化...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 仮想環境の有効化に失敗しました
    echo 仮想環境が存在しない場合は以下を実行してください：
    echo python -m venv venv
    pause
    exit /b 1
)
echo ✅ 仮想環境が有効化されました

REM 2. 依存関係の確認
echo.
echo [2/6] 依存関係の確認...
python -c "import numpy, torch, stable_baselines3, optuna; print('✅ 依存関係確認完了')"
if errorlevel 1 (
    echo ❌ 依存関係の確認に失敗しました
    echo 以下のコマンドで依存関係をインストールしてください：
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM 3. データの確認
echo.
echo [3/6] データの確認...
if not exist "kyotei_predictor\data\raw\2024-01" (
    echo ❌ 2024年1月データが見つかりません
    echo データディレクトリを確認してください
    pause
    exit /b 1
)
echo ✅ 2024年1月データが確認されました

REM 4. 実行モードの選択
echo.
echo [4/6] 実行モードの選択...
echo.
echo 実行モードを選択してください:
echo 1. テストモード（短時間、3試行）
echo 2. 本番モード（長時間、50試行）
echo.
set /p choice="選択 (1-2): "

if "%choice%"=="1" (
    echo テストモードで実行します...
    set TRIALS=3
    set TEST_MODE=--test-mode
    set MODE_NAME=テストモード
) else if "%choice%"=="2" (
    echo 本番モードで実行します...
    set TRIALS=50
    set TEST_MODE=
    set MODE_NAME=本番モード
) else (
    echo 無効な選択です。1または2を選択してください。
    pause
    exit /b 1
)

REM 5. 最適化の実行
echo.
echo [5/6] 最適化の実行...
echo %MODE_NAME%で最適化を開始します（%TRIALS%試行）
echo.

REM 最適化の実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --n-trials %TRIALS% %TEST_MODE%

if errorlevel 1 (
    echo.
    echo ❌ 最適化の実行に失敗しました
    pause
    exit /b 1
)

REM 6. 自動クリーンアップ
echo.
echo [6/6] 自動クリーンアップの実行...
echo 古いファイルの削除を開始します...
python kyotei_predictor\tools\maintenance\auto_cleanup.py

if errorlevel 1 (
    echo ❌ 自動クリーンアップでエラーが発生しました
) else (
    echo ✅ 自動クリーンアップが完了しました
)

echo.
echo ========================================
echo ✅ 最適化が正常に完了しました
echo ========================================
echo.
echo 実行モード: %MODE_NAME%
echo 試行回数: %TRIALS%
echo 自動クリーンアップ: 実行済み
echo.
echo 結果ファイル:
echo - optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json
echo - optuna_studies/graduated_reward_optimization_YYYYMMDD_HHMMSS.db
echo.
pause 