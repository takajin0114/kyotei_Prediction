@echo off
echo === 2024年3月データでの段階的報酬最適化テスト ===
echo.

echo ステップ1: Python環境の確認
python --version
if %errorlevel% neq 0 (
    echo ❌ Pythonが見つかりません
    pause
    exit /b 1
)

echo.
echo ステップ2: モジュールのインポートテスト
python -c "import numpy; print('✅ numpy OK')"
python -c "import optuna; print('✅ optuna OK')"
python -c "from stable_baselines3 import PPO; print('✅ stable_baselines3 OK')"

echo.
echo ステップ3: データディレクトリの確認
if exist "kyotei_predictor\data\raw\2024-03" (
    echo ✅ 2024年3月データディレクトリ存在
) else (
    echo ❌ 2024年3月データディレクトリ不存在
    pause
    exit /b 1
)

echo.
echo ステップ4: 最適化テストの実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir "kyotei_predictor/data/raw/2024-03" --n-trials 1 --study-name "test_202403_batch" --test-mode

echo.
echo ✅ テスト完了
pause 