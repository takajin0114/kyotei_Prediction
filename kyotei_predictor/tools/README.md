# tools ディレクトリ README

**最終更新日: 2025-07-03**

---

## 本READMEの役割
- tools/配下の各種ツール群（fetch, batch, analysis, viz, ai, common）の役割・使い方を記載
- サブディレクトリごとの説明・設計書へのリンクを明記
- ルートREADMEやNEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../README.md](../../README.md)（全体概要・セットアップ・タスク入口）
- [../../NEXT_STEPS.md](../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../integration_design.md](../../integration_design.md)（統合設計・アーキテクチャ）
- [../../prediction_algorithm_design.md](../../prediction_algorithm_design.md)（予測アルゴリズム設計）
- [../../site_analysis.md](../../site_analysis.md)（データ取得元サイト分析）
- [../../web_app_requirements.md](../../web_app_requirements.md)（Webアプリ要件・UI設計）

---

# 以下、従来の内容（各サブディレクトリの説明・使い方など）を現状維持・必要に応じて最新化

# Tools Directory

競艇予測プラットフォームの各種ツール群です。用途別にサブディレクトリに整理されています。

## 📁 ディレクトリ構成

### `fetch/` - データ取得ツール
- `race_data_fetcher.py` - レースデータ取得
- `odds_fetcher.py` - オッズデータ取得  
- `fetch_new_race.py` - 新規レース取得

### `batch/` - バッチ処理ツール
- `batch_data_fetcher.py` - 基本バッチデータ取得
- `batch_fetch_by_schedule.py` - スケジュールベースバッチ取得
- `batch_fetch_all_venues.py` - 全会場バッチ取得

### `analysis/` - データ分析ツール
- `odds_analysis.py` - オッズ分析

### `viz/` - 可視化ツール
- `data_display.py` - データ表示
- `html_display.py` - HTML表示
- `rl_visualization.py` - RL可視化

### `ai/` - AI・最適化ツール
- `optuna_optimizer.py` - Optuna最適化
- `test_optuna_setup.py` - Optuna設定テスト
- `rl_learn_sample.py` - RL学習サンプル

### `common/` - 共通・マッピングツール
- `venue_mapping.py` - 会場マッピング

## 🚀 使用方法

### データ取得
```bash
# 単発データ取得
python tools/fetch/race_data_fetcher.py
python tools/fetch/odds_fetcher.py

# バッチデータ取得
python tools/batch/batch_fetch_all_venues.py
```

### 分析・可視化
```bash
# データ分析
python tools/analysis/odds_analysis.py

# 可視化
python tools/viz/data_display.py
python tools/viz/html_display.py
```

### AI・最適化
```bash
# Optuna最適化
python tools/ai/optuna_optimizer.py

# RL学習
python tools/ai/rl_learn_sample.py
```

## 📝 開発ガイドライン

- 各ツールは独立して動作するよう設計
- 共通処理は`common/`に集約
- 引数・出力・エラー処理は統一
- ログ・進捗表示は標準化 