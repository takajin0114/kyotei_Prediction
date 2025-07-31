@echo off
REM 最適化実行の前段準備を含むバッチファイル
REM 2024年1月データでの本番最適化実行

echo ========================================
echo 競艇予測モデル最適化実行バッチ
echo ========================================
echo.

REM 1. 仮想環境の有効化
echo [1/4] 仮想環境の有効化...
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
echo [2/4] 依存関係の確認...
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
echo [3/4] データの確認...
if not exist "kyotei_predictor\data\raw\2024-01" (
    echo ❌ 2024年1月データが見つかりません
    echo データディレクトリを確認してください
    pause
    exit /b 1
)
echo ✅ 2024年1月データが確認されました

REM 4. 最適化の実行
echo.
echo [4/4] 最適化の実行...
echo 本番モードで最適化を開始します（50試行）
echo 実行時間: 数時間予定
echo.

REM 最適化の実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --n-trials 50

if errorlevel 1 (
    echo.
    echo ❌ 最適化の実行に失敗しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 最適化が正常に完了しました
echo ========================================
echo.
echo 結果ファイル:
echo - optuna_results/graduated_reward_optimization_YYYYMMDD_HHMMSS.json
echo - optuna_studies/graduated_reward_optimization_YYYYMMDD_HHMMSS.db
echo.
pause 