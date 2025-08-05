@echo off
echo ========================================
echo 全学習関連ファイル削除（学習履歴含む）
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

echo.
echo 削除対象ファイル・ディレクトリ:
echo - optuna_logs/ (学習ログ)
echo - optuna_models/ (学習済みモデル)
echo - optuna_tensorboard/ (TensorBoardログ)
echo - optuna_studies/ (学習履歴DB)
echo - optuna_results/ (最適化結果)
echo - outputs/logs/ (デバッグログ)
echo - outputs/*.json (評価結果)
echo - outputs/*.png (評価グラフ)
echo - monitoring/performance_history.json.gz (性能履歴)
echo - alerts/ (アラートファイル)
echo.
echo ⚠️  警告: この操作は学習履歴も含めてすべて削除します
echo.

set /p confirm="本当に削除を実行しますか？ (y/N): "
if /i "%confirm%"=="y" (
    echo.
    echo 削除を開始します...
    
    REM optuna_logs 削除
    if exist optuna_logs (
        echo optuna_logs を削除中...
        rmdir /s /q optuna_logs
        echo ✓ optuna_logs 削除完了
    )
    
    REM optuna_models 削除
    if exist optuna_models (
        echo optuna_models を削除中...
        rmdir /s /q optuna_models
        echo ✓ optuna_models 削除完了
    )
    
    REM optuna_tensorboard 削除
    if exist optuna_tensorboard (
        echo optuna_tensorboard を削除中...
        rmdir /s /q optuna_tensorboard
        echo ✓ optuna_tensorboard 削除完了
    )
    
    REM optuna_studies 削除
    if exist optuna_studies (
        echo optuna_studies を削除中...
        rmdir /s /q optuna_studies
        echo ✓ optuna_studies 削除完了
    )
    
    REM optuna_results 削除
    if exist optuna_results (
        echo optuna_results を削除中...
        rmdir /s /q optuna_results
        echo ✓ optuna_results 削除完了
    )
    
    REM outputs/logs 削除
    if exist outputs\logs (
        echo outputs/logs を削除中...
        rmdir /s /q outputs\logs
        echo ✓ outputs/logs 削除完了
    )
    
    REM outputs 内のJSON・PNGファイル削除
    if exist outputs\*.json (
        echo outputs/*.json を削除中...
        del /q outputs\*.json
        echo ✓ outputs/*.json 削除完了
    )
    
    if exist outputs\*.png (
        echo outputs/*.png を削除中...
        del /q outputs\*.png
        echo ✓ outputs/*.png 削除完了
    )
    
    REM monitoring ファイル削除
    if exist monitoring\performance_history.json.gz (
        echo monitoring/performance_history.json.gz を削除中...
        del /q monitoring\performance_history.json.gz
        echo ✓ monitoring/performance_history.json.gz 削除完了
    )
    
    REM alerts 削除
    if exist alerts (
        echo alerts を削除中...
        rmdir /s /q alerts
        echo ✓ alerts 削除完了
    )
    
    echo.
    echo ========================================
    echo 全削除完了
    echo ========================================
    echo.
    echo 注意: 学習履歴も含めてすべて削除されました
    echo 次回の学習は最初から開始されます
) else (
    echo.
    echo 削除をキャンセルしました。
) 