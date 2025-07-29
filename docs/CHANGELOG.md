# Changelog

## [Unreleased] - 2025-07-29

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