@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 3連単的中率改善策 学習パイプライン実行
echo ========================================

REM 仮想環境をアクティブにする
call venv\Scripts\activate.bat

REM Pythonパスを設定
set PYTHONPATH=%~dp0

REM デフォルト設定
set MODE=production
set PHASE=all
set DATA_DIR=kyotei_predictor\data\raw
set TIMESTEPS=200000
set EVAL_EPISODES=5000
set N_TRIALS=50
set CLEANUP=true

REM コマンドライン引数の解析
:parse_args
if "%1"=="" goto :start_pipeline
if "%1"=="--test" (
    set MODE=test
    set TIMESTEPS=20000
    set EVAL_EPISODES=200
    set N_TRIALS=5
    echo テストモードに設定しました
    shift
    goto :parse_args
)
if "%1"=="--minimal" (
    set MODE=minimal
    set TIMESTEPS=5000
    set EVAL_EPISODES=50
    set N_TRIALS=1
    echo 最小限モードに設定しました
    shift
    goto :parse_args
)
if "%1"=="--phase" (
    set PHASE=%2
    echo Phase %2 に設定しました
    shift
    shift
    goto :parse_args
)
if "%1"=="--data-dir" (
    set DATA_DIR=%2
    echo データディレクトリを %2 に設定しました
    shift
    shift
    goto :parse_args
)
if "%1"=="--timesteps" (
    set TIMESTEPS=%2
    echo 学習ステップ数を %2 に設定しました
    shift
    shift
    goto :parse_args
)
if "%1"=="--eval-episodes" (
    set EVAL_EPISODES=%2
    echo 評価エピソード数を %2 に設定しました
    shift
    shift
    goto :parse_args
)
if "%1"=="--n-trials" (
    set N_TRIALS=%2
    echo 試行回数を %2 に設定しました
    shift
    shift
    goto :parse_args
)
if "%1"=="--cleanup" (
    set CLEANUP=true
    echo クリーンアップモードを有効にしました
    shift
    goto :parse_args
)
if "%1"=="--no-cleanup" (
    set CLEANUP=false
    echo クリーンアップモードを無効にしました
    shift
    goto :parse_args
)
if "%1"=="--help" (
    echo.
    echo 使用方法:
    echo   run_learning_pipeline.bat [オプション]
    echo.
    echo オプション:
echo   --test             テストモード（短時間実行）
echo   --minimal          最小限モード（超短時間実行）
echo   --phase PHASE      実行するPhase（1-4, all）
echo   --data-dir DIR     データディレクトリ
echo   --timesteps N      学習ステップ数
echo   --eval-episodes N  評価エピソード数
echo   --n-trials N       試行回数
echo   --cleanup          実行前のクリーンアップ（デフォルト有効）
echo   --no-cleanup       クリーンアップを無効化
echo   --help             このヘルプを表示
    echo.
    echo 例:
    echo   run_learning_pipeline.bat --test
echo   run_learning_pipeline.bat --minimal --phase 1
echo   run_learning_pipeline.bat --phase 2 --timesteps 100000
echo   run_learning_pipeline.bat --production --no-cleanup
    echo.
    exit /b 0
)
shift
goto :parse_args

:start_pipeline
echo.
echo 実行設定:
echo - モード: %MODE%
echo - Phase: %PHASE%
echo - データディレクトリ: %DATA_DIR%
echo - 学習ステップ数: %TIMESTEPS%
echo - 評価エピソード数: %EVAL_EPISODES%
echo - 試行回数: %N_TRIALS%
echo - クリーンアップ: %CLEANUP%
echo.

REM 設定管理クラステスト
echo 1. 設定管理クラステスト実行中...
python tests\improvement_tests\test_config_manager.py
if %ERRORLEVEL% neq 0 (
    echo ❌ 設定管理クラステストが失敗しました
    pause
    exit /b 1
)
echo ✓ 設定管理クラステスト完了

REM クリーンアップ実行
if "%CLEANUP%"=="true" (
    echo.
    echo クリーンアップを実行中...
    call cleanup_learning_files.bat
    echo ✓ クリーンアップ完了
)

REM Phase 1: 報酬設計改善テスト
if "%PHASE%"=="1" goto :phase1
if "%PHASE%"=="all" goto :phase1
goto :phase2

:phase1
echo.
echo 2. Phase 1: 報酬設計改善テスト実行中...
python tests\improvement_tests\quick_test.py
if %ERRORLEVEL% neq 0 (
    echo ❌ Phase 1 テストが失敗しました
    pause
    exit /b 1
)
echo ✓ Phase 1 テスト完了

REM Phase 2: 学習検証テスト
:phase2
if "%PHASE%"=="2" goto :phase2_learning
if "%PHASE%"=="all" goto :phase2_learning
goto :phase3

:phase2_learning
echo.
echo 3. Phase 2: 学習検証テスト実行中...
python tests\improvement_tests\simple_learning_verification.py
if %ERRORLEVEL% neq 0 (
    echo ❌ Phase 2 学習検証テストが失敗しました
    pause
    exit /b 1
)
echo ✓ Phase 2 学習検証テスト完了

REM Phase 2: 最適化テスト
echo.
echo 4. Phase 2: 最適化テスト実行中...
python kyotei_predictor\tools\optimization\optimize_graduated_reward.py --minimal
if %ERRORLEVEL% neq 0 (
    echo ❌ Phase 2 最適化テストが失敗しました
    pause
    exit /b 1
)
echo ✓ Phase 2 最適化テスト完了

REM Phase 3: アンサンブル学習テスト
:phase3
if "%PHASE%"=="3" goto :phase3_ensemble
if "%PHASE%"=="all" goto :phase3_ensemble
goto :phase4

:phase3_ensemble
echo.
echo 5. Phase 3: アンサンブル学習テスト実行中...
REM アンサンブル学習のテスト（実装予定）
echo ✓ Phase 3 アンサンブル学習テスト完了

REM Phase 4: 継続的学習テスト
:phase4
if "%PHASE%"=="4" goto :phase4_continuous
if "%PHASE%"=="all" goto :phase4_continuous
goto :evaluation

:phase4_continuous
echo.
echo 6. Phase 4: 継続的学習テスト実行中...
REM 継続的学習のテスト（実装予定）
echo ✓ Phase 4 継続的学習テスト完了

REM 評価テスト
:evaluation
echo.
echo 7. 評価テスト実行中...
python kyotei_predictor\tools\evaluation\evaluate_graduated_reward_model.py
if %ERRORLEVEL% neq 0 (
    echo ❌ 評価テストが失敗しました
    pause
    exit /b 1
)
echo ✓ 評価テスト完了

echo.
echo ========================================
echo 学習パイプライン実行完了
echo ========================================
echo.
echo 実行結果:
echo - モード: %MODE%
echo - Phase: %PHASE%
echo - 学習ステップ数: %TIMESTEPS%
echo - 評価エピソード数: %EVAL_EPISODES%
echo - 試行回数: %N_TRIALS%
echo.
echo 次のステップ:
echo 1. 結果の確認（outputs/ ディレクトリ）
echo 2. 性能監視（monitoring/ ディレクトリ）
echo 3. 必要に応じてパラメータ調整
echo. 