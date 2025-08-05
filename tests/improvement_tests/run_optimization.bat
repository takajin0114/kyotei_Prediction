@echo off
echo ========================================
echo 最適化実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM 最適化を実行（最小限モード）
python kyotei_predictor\tools\optimization\optimize_graduated_reward.py --minimal

echo.
echo ========================================
echo 最適化完了
echo ======================================== 