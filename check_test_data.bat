@echo off
chcp 65001 >nul
echo ========================================
echo test_rawディレクトリのデータ確認
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM データ確認スクリプトを実行
python check_test_data.py

echo.
echo ========================================
echo データ確認完了
echo ======================================== 