@echo off
chcp 65001 >nul
echo ========================================
echo 的中率詳細分析機能のテスト実行
echo ========================================

REM 仮想環境の有効化
echo 仮想環境を有効化しています...
call venv\Scripts\activate.bat

REM テスト実行
echo.
echo ========================================
echo 的中率詳細分析機能のテストを開始します...
echo ========================================
python kyotei_predictor\tests\test_hit_rate_analysis.py

if %errorlevel% neq 0 (
    echo テスト実行中にエラーが発生しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 的中率詳細分析機能のテスト完了
echo ========================================
echo.
echo テスト結果:
echo - 機能テスト: 完了
echo - 的中率計算: 完了
echo - 可視化機能: 完了
echo. 