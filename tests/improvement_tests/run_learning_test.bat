@echo off
chcp 65001 >nul
echo ========================================
echo 学習テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テスト用データディレクトリを設定
set DATA_DIR=kyotei_predictor/data/test_raw

REM 学習検証テストを実行
python simple_learning_verification.py

echo.
echo ========================================
echo 学習テスト完了
echo ======================================== 