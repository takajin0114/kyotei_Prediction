@echo off
echo ========================================
echo クイックテスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テストディレクトリに移動してクイックテストを実行
cd tests\improvement_tests
python quick_test.py

echo.
echo ========================================
echo クイックテスト完了
echo ======================================== 