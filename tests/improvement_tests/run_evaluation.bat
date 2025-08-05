@echo off
echo ========================================
echo 評価実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM 評価を実行
python kyotei_predictor\tools\evaluation\evaluate_graduated_reward_model.py

echo.
echo ========================================
echo 評価完了
echo ======================================== 