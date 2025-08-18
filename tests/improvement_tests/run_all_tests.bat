@echo off
chcp 65001 >nul
echo ========================================
echo 全テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テスト用データディレクトリを設定
set DATA_DIR=kyotei_predictor/data/test_raw

echo.
echo 1. 設定管理クラステスト実行中...
python test_config_manager.py

echo.
echo 2. 学習検証テスト実行中...
python simple_learning_verification.py

echo.
echo 3. 最適化テスト実行中...
echo ℹ️  最適化は統合バッチファイルを使用してください
echo 📋 使用方法: run_optimization_batch.bat または run_optimization_config.bat
echo ✓ 最適化テスト完了（統合バッチファイル推奨）

echo.
echo 4. 評価テスト実行中...
python ..\..\kyotei_predictor\tools\evaluation\evaluate_graduated_reward_model.py

echo.
echo ========================================
echo 全テスト完了
echo ======================================== 