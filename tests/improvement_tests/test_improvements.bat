@echo off
echo ========================================
echo 3連単的中率改善策テスト実行
echo ========================================

REM 仮想環境の有効化
echo 仮想環境を有効化中...
call venv\Scripts\activate.bat

REM 環境確認
echo.
echo 環境確認中...
python -c "import sys; print('Python version:', sys.version)"
python -c "import gymnasium; print('Gymnasium version:', gymnasium.__version__)"
python -c "import stable_baselines3; print('Stable-Baselines3 version:', stable_baselines3.__version__)"

REM Phase 1: 報酬設計の改善テスト
echo.
echo ========================================
echo Phase 1: 報酬設計の改善テスト
echo ========================================
python -c "
import sys
sys.path.append('kyotei_predictor')
from pipelines.kyotei_env import calc_trifecta_reward, calc_trifecta_reward_improved
import logging

# テストデータ
test_action = 0  # 1-2-3の組み合わせ
test_arrival = (1, 2, 3)  # 的中
test_odds = [{'betting_numbers': [1, 2, 3], 'ratio': 10.0}]
test_bet = 100

# 旧報酬と新報酬の比較
old_reward = calc_trifecta_reward(test_action, test_arrival, test_odds, test_bet)
new_reward = calc_trifecta_reward_improved(test_action, test_arrival, test_odds, test_bet)

print(f'旧報酬設計: {old_reward}')
print(f'新報酬設計: {new_reward}')
print(f'改善効果: {new_reward - old_reward}')
"

REM Phase 2: 学習時間延長のテスト（最小スコープ）
echo.
echo ========================================
echo Phase 2: 学習時間延長テスト（最小スコープ）
echo ========================================
python kyotei_predictor/tools/optimization/optimize_graduated_reward.py --test-mode --minimal

REM テスト結果の確認
echo.
echo ========================================
echo テスト結果確認
echo ========================================
if exist "kyotei_predictor/outputs" (
    echo 出力ディレクトリの内容:
    dir kyotei_predictor\outputs /b
)

if exist "optuna_results" (
    echo Optuna結果ファイル:
    dir optuna_results\*.json /b
)

echo.
echo ========================================
echo テスト完了
echo ========================================
pause 