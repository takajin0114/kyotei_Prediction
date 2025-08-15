@echo off
chcp 65001 >nul
echo ========================================
echo 改善策テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テスト用データディレクトリを設定
set DATA_DIR=kyotei_predictor/data/test_raw

REM テストディレクトリに移動してテストを実行
cd tests\improvement_tests
call run_all_tests.bat

echo.
echo ========================================
echo テスト完了
echo ======================================== 