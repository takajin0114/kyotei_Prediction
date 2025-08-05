@echo off
echo ========================================
echo 学習関連ファイル削除
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

echo.
echo 削除対象ファイル・ディレクトリ:
echo - optuna_logs/ (学習ログ)
echo - optuna_models/ (学習済みモデル)
echo - optuna_tensorboard/ (TensorBoardログ)
echo - outputs/logs/ (デバッグログ)
echo - outputs/*.json (評価結果)
echo - outputs/*.png (評価グラフ)
echo - monitoring/performance_history.json.gz (性能履歴)
echo - alerts/ (アラートファイル)
echo.

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
echo 削除完了
echo ========================================

echo.
echo 注意: optuna_studies/ と optuna_results/ は保持されています
echo これらは学習履歴として重要なので手動で削除してください 