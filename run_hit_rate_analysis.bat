@echo off
chcp 65001 >nul
echo ========================================
echo 的中率詳細分析実行
echo ========================================

REM 仮想環境の有効化
echo 仮想環境を有効化しています...
call venv\Scripts\activate.bat

REM 的中率詳細分析実行
echo.
echo ========================================
echo 的中率詳細分析を開始します...
echo ========================================
python kyotei_predictor\tools\evaluation\analyze_hit_rate_detailed.py --model-path "optuna_models\trial_49\checkpoint_1024_steps.zip" --n-eval-episodes 100 --data-dir "kyotei_predictor/data/raw/2024-02" --top-n-list 10 20

if %errorlevel% neq 0 (
    echo 的中率詳細分析中にエラーが発生しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 的中率詳細分析完了
echo ========================================
echo.
echo 結果ファイル:
echo - 詳細分析結果: outputs/detailed_hit_rate_analysis_*.json
echo - 可視化結果: outputs/detailed_hit_rate_analysis_plots_*.png
echo. 