@echo off
echo ========================================
echo 学習関連ファイル ディスク使用量確認
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

echo.
echo 各ディレクトリのサイズを確認中...
echo.

REM 各ディレクトリのサイズを確認
if exist optuna_logs (
    for /f "tokens=3" %%a in ('dir optuna_logs /s ^| find "File(s)"') do (
        echo optuna_logs: %%a
    )
) else (
    echo optuna_logs: 存在しません
)

if exist optuna_models (
    for /f "tokens=3" %%a in ('dir optuna_models /s ^| find "File(s)"') do (
        echo optuna_models: %%a
    )
) else (
    echo optuna_models: 存在しません
)

if exist optuna_tensorboard (
    for /f "tokens=3" %%a in ('dir optuna_tensorboard /s ^| find "File(s)"') do (
        echo optuna_tensorboard: %%a
    )
) else (
    echo optuna_tensorboard: 存在しません
)

if exist optuna_studies (
    for /f "tokens=3" %%a in ('dir optuna_studies /s ^| find "File(s)"') do (
        echo optuna_studies: %%a
    )
) else (
    echo optuna_studies: 存在しません
)

if exist optuna_results (
    for /f "tokens=3" %%a in ('dir optuna_results /s ^| find "File(s)"') do (
        echo optuna_results: %%a
    )
) else (
    echo optuna_results: 存在しません
)

if exist outputs (
    for /f "tokens=3" %%a in ('dir outputs /s ^| find "File(s)"') do (
        echo outputs: %%a
    )
) else (
    echo outputs: 存在しません
)

if exist monitoring (
    for /f "tokens=3" %%a in ('dir monitoring /s ^| find "File(s)"') do (
        echo monitoring: %%a
    )
) else (
    echo monitoring: 存在しません
)

if exist alerts (
    for /f "tokens=3" %%a in ('dir alerts /s ^| find "File(s)"') do (
        echo alerts: %%a
    )
) else (
    echo alerts: 存在しません
)

echo.
echo ========================================
echo 確認完了
echo ======================================== 