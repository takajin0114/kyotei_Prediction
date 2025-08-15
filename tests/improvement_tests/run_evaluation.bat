@echo off
chcp 65001 >nul
echo ========================================
echo 評価テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テスト用データディレクトリを設定
set DATA_DIR=kyotei_predictor/data/test_raw

REM 評価スクリプトを実行
python ..\..\kyotei_predictor\tools\evaluation\evaluate_graduated_reward_model.py

echo.
echo ========================================
echo 評価テスト完了
echo ======================================== 