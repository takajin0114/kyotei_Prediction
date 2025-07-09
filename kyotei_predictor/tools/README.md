# tools ディレクトリ README

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- tools/配下の各種ツール群（fetch, batch, analysis, viz, ai, common）の役割・使い方・運用ルールを記載
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

## サブディレクトリ構成と役割

- `fetch/` : データ取得ツール（公式サイトからのスクレイピング、API取得など）
- `batch/` : バッチ処理ツール（大量データの自動収集・スケジュール取得など）
- `analysis/` : データ分析・検証ツール（オッズ分析、データ検証、バッチ結果チェックなど）
- `viz/` : 可視化・表示ツール（データ・学習結果のグラフ化、HTML表示など）
- `ai/` : AI・強化学習・Optuna最適化ツール（学習・最適化・評価・可視化など）
- `common/` : 共通ユーティリティ・会場マッピング・設定管理

---

## 運用ルール・整理方針
- 各サブディレクトリのREADMEに用途・使い方・注意点を明記
- 共通処理・定数・マッピングはcommon/に集約
- 不要なファイルや重複は定期的に整理・削除
- 新規ツールは用途に応じて適切なサブディレクトリに追加
- ルートREADMEや設計書との整合性を保つ

---

## 不要・重複ファイルの確認
- 現状、fetch/batch/analysis/viz/ai/common 以外の用途外ファイル・重複はありません
- __pycache__/はPythonのキャッシュであり、.gitignore対象です
- 不要なファイルが発生した場合は随時整理してください

## batchディレクトリの主要スクリプト
- batch_fetch_all_venues.py : 全会場バッチ取得（標準・並列版）
- fast_future_entries_fetcher.py : 高速未来レース取得
- retry_missing_races.py : 欠損レース再取得

## 運用ルール
- 既存ファイルの重複取得を避ける
- レート制限・エラーハンドリングを徹底
- 不要な一時ファイルは随時削除

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

## batch_fetch_all_venues.py の使い方（2024年7月更新）

全会場・全レースのデータを並列で取得するバッチです。

### 実行例

```sh
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date 2024-06-01 --end-date 2024-06-30 --stadiums KIRYU,EDOGAWA
```

- `--start-date` : 取得開始日（YYYY-MM-DD, 必須）
- `--end-date`   : 取得終了日（YYYY-MM-DD, 必須）
- `--stadiums`   : 対象会場名（カンマ区切り, 必須, 例: KIRYU,EDOGAWA,...）

会場名は大文字で指定してください。

**全会場を指定したい場合は `--stadiums ALL` でOKです。**

```sh
python -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date 2024-06-01 --end-date 2024-06-30 --stadiums ALL
```

引数が未指定の場合はエラーとなり、バッチは実行されません。

### 選手名解析エラーの最新対応方針（2024/07/08）

- 選手名が「姓 名」形式でsplitできない場合（ValueError発生時）は、
  - 姓 = フルネーム、名 = 空文字 として暫定的に処理します。
  - さらに、そのフルネームを `error_racer_names.log` に追記し、後から調査できるようにします。
- エラー発生時は標準出力にも該当選手名文字列を出力し、即時デバッグ可能としています。
- これにより、データ欠損を最小限に抑えつつ、想定外のデータ形式も記録・追跡できます。

#### 実装例（抜粋）
```python
try:
    racer_last_name, racer_first_name = re.split(r"[　 ]+", racer_full_name)
except ValueError:
    with open("error_racer_names.log", "a", encoding="utf-8") as logf:
        logf.write(f"[extract_racers] Unexpected name format: '{racer_full_name}'\n")
    racer_last_name = racer_full_name
    racer_first_name = ""
```

- 詳細は `kyotei_predictor/tools/fetch/race_data_fetcher.py` および metaboatrace側 `extract_racers` 実装を参照。 