@echo off
chcp 65001 >nul
echo ========================================
echo 最適化テスト実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM テスト用データディレクトリを設定
set DATA_DIR=kyotei_predictor/data/test_raw

REM 最適化スクリプトを実行
python ..\..\kyotei_predictor\tools\optimization\optimize_graduated_reward.py --minimal

echo.
echo ========================================
echo 最適化テスト完了
echo ======================================== 