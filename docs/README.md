# kyotei_Prediction プロジェクト

競艇レースの予測システムを構築するプロジェクトです。

## 📋 プロジェクト概要

- **目的**: 競艇レースの3連単予測システムの構築・運用
- **現在の状況**: 予想ツールとしての実装完了、Web表示機能実装中
- **最終目標**: 深夜自動実行による完全自動化システム

## 🎯 主要機能

### ✅ 実装完了
- **データ取得システム**: バッチ処理による自動データ取得
- **予想ツール**: 3連単予測、購入方法提案、JSON保存機能
- **モデル開発**: PPOモデル、Optuna最適化、特徴量分析
- **品質管理**: 自動品質チェック、異常検知

### 🔄 実装中
- **Web表示機能**: 静的HTMLでの予測結果表示

### 📋 計画中
- **深夜自動実行**: スケジューラ設定、運用監視

## 📚 主要ドキュメント

### 現在の状況
- [CURRENT_STATUS_SUMMARY.md](CURRENT_STATUS_SUMMARY.md) - プロジェクト全体の現在の状況サマリー
- [NEXT_STEPS.md](NEXT_STEPS.md) - 直近のTODO・優先度・進捗

### 予想ツール
- [PREDICTION_TOOL_ROADMAP.md](PREDICTION_TOOL_ROADMAP.md) - 予想ツール運用ロードマップ
- [PREDICTION_TOOL_IMPLEMENTATION_TASKS.md](PREDICTION_TOOL_IMPLEMENTATION_TASKS.md) - 実装タスク詳細

### システム・運用
- [BATCH_SYSTEM_CURRENT_STATUS.md](BATCH_SYSTEM_CURRENT_STATUS.md) - バッチシステム状況
- [SCHEDULED_MAINTENANCE_GUIDE.md](SCHEDULED_MAINTENANCE_GUIDE.md) - スケジューラ化運用
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - 開発ロードマップ

### 技術仕様
- [data_acquisition.md](data_acquisition.md) - データ取得仕様
- [site_analysis.md](site_analysis.md) - サイト分析

## 🚀 クイックスタート

### 予想ツールの実行
```bash
# 完全統合実行
python -m kyotei_predictor.tools.prediction_tool --date 2024-07-12

# 特定会場のみ実行
python -m kyotei_predictor.tools.prediction_tool --date 2024-07-12 --venues KIRYU TAMAGAWA
```

### データ取得の実行
```bash
# 一括データ取得
python -m kyotei_predictor.tools.run_data_maintenance
```

## 📊 最新の進捗（2025-07-13）

- ✅ **予想ツール実装完了**: 統合実行フロー、3連単予測、購入方法提案、JSON保存機能
- ✅ **テスト成功**: TAMAGAWA会場12レースでの予測成功確認
- 🔄 **Web表示機能実装中**: 静的HTMLファイルでの予測結果表示
- 🔄 **2024年3月データ取得進行中**: 8並列処理で安定実行中

## 📝 更新履歴

- **2025-07-13**: 予想ツール実装完了、テスト成功確認
- **2025-07-11**: 予想ツール仕様確定、購入方法提案機能追加
- **2025-01-XX**: バッチシステム改善、進捗表示修正 