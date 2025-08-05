@echo off
echo ========================================
echo 設定管理クラステスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM 設定管理クラステストを実行
python test_config_manager.py

echo.
echo ========================================
echo テスト完了
echo ======================================== 