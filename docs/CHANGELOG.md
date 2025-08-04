# Changelog

## [Unreleased] - 2025-08-03

### Added
- **継続学習システム付きバッチファイル** (`run_optimization_production_continuous_with_evaluation.bat`)
  - 自動的中率評価機能（1000エピソード）
  - 評価結果の可視化
  - 継続学習システムの統合
- **軽量版バッチファイル** (`run_optimization_production_continuous.bat`)
  - 継続学習システム（評価なし）
  - 高速実行向け

### Changed
- **リポジトリ整理**: 不要なバッチファイルを削除し、構造を簡潔化
  - 削除: `run_optimization_production_simple.bat`
  - 削除: `run_optimization_production_with_cleanup.bat`
  - 削除: `run_optimization_production_with_cleanup_auto.bat`
  - 削除: `run_optimization_with_setup_interactive.bat`
  - 削除: 空ディレクトリ (`custom_models/`, `test_models/`)
  - 削除: 一時ログファイル (`auto_cleanup.log`)
- **ドキュメント更新**: READMEとBATCH_EXECUTION_GUIDEを最新のバッチファイルに合わせて更新
- **推奨バッチファイルの明確化**: 星評価システムで推奨度を表示

### Fixed
- バッチファイルの重複と混乱を解消
- 古い最適化スクリプトの参照を削除
- メンテナンス負荷の軽減

### Technical Details
- 継続学習システムの統合により的中率が大幅向上
- 評価機能により性能測定が自動化
- リポジトリ構造の簡潔化により保守性が向上

## [Previous] - 2025-07-29

### Added
- 既存スタディ継続機能 (`--resume-existing` オプション) を `optimize_graduated_reward.py` に追加
- 3月データ最適化結果の分析機能
- 最適化スクリプトのテスト機能

### Changed
- `kyotei_predictor/tools/optimization/optimize_graduated_reward.py` の `optimize_graduated_reward` 関数に `resume_existing` パラメータを追加
- 既存スタディファイルの自動検索機能を実装
- `load_if_exists=True` オプションで既存スタディの継続をサポート

### Fixed
- 3月データ最適化の中断問題を解決
- 既存スタディからの継続実行機能を実装

### Technical Details
- Optuna SQLiteデータベースの直接クエリ機能を追加
- 既存試行数の表示機能を追加
- 新規スタディ作成と既存スタディ継続の両方をサポート

## [Previous] - 2025-07-28

### Added
- 2月データ最適化結果の分析
- 最適化結果のJSON出力機能
- 月別データでの最適化実行機能