@echo off
echo ========================================
echo 学習検証テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM 学習検証テストを実行
python simple_learning_verification.py

echo.
echo ========================================
echo テスト完了
echo ======================================== 