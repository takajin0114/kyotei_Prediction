# pipelines ディレクトリ README

> **注記**: 詳細な設計・運用ルール・全体像は[../../docs/README.md](../../docs/README.md)・[../../README.md](../../README.md)・各設計書を参照してください。

## 参照フロー・索引
- パイプライン全体像・運用ルール: [../../docs/integration_design.md](../../docs/integration_design.md)
- データ取得・前処理・分析の流れ: [../../docs/data_acquisition.md](../../docs/data_acquisition.md)
- 開発計画・進行中タスク: [../../docs/DEVELOPMENT_ROADMAP.md](../../docs/DEVELOPMENT_ROADMAP.md)
- 各ツール・バッチ: [../tools/README.md](../tools/README.md)

## 概要
- データ前処理・特徴量生成・AI学習環境などパイプラインの主要スクリプトを集約
- 詳細な設計・運用ルールはdocs/配下に集約

## 主なスクリプト
- `data_preprocessor.py` : データ前処理・クリーニング（バッチ一括対応）
- `feature_enhancer.py` : 特徴量エンジニアリング
- `feature_analysis.py` : 特徴量分布・相関・重要度自動分析
- `kyotei_env.py` : 強化学習用環境クラス
- `trifecta_probability.py` : 3連単確率計算
- `db_integration.py` : DB連携・一括インポート

## 推奨パイプライン分析フロー
1. データ取得（run_data_maintenance.py等でraw/にrace_data_*.jsonを保存）
2. `data_preprocessor.py`で一括前処理（feature_data.csv等を生成）
3. `feature_analysis.py`で分布・相関・重要度を自動分析・可視化
4. 必要に応じて特徴量設計・前処理を改善

---

## 📋 一括処理・運用手順（実運用フロー）

### 1. データ取得
- 生データは `kyotei_predictor/data/raw/` に `race_data_*.json` 形式で保存

### 2. 前処理バッチ実行
```bash
python kyotei_predictor/pipelines/data_preprocessor.py --input-dir kyotei_predictor/data/raw --output kyotei_predictor/data/processed/feature_data.csv
```
- テスト用: `--max-files 100` などで件数制限可

### 3. 特徴量分析バッチ実行
```bash
python kyotei_predictor/pipelines/feature_analysis.py --input kyotei_predictor/data/processed/feature_data.csv --output-dir outputs/feature_analysis
```
- 出力: 欠損率・統計量・相関・カテゴリ分布・重要度（CSV/PNG/HTML等）

### 4. 推奨ディレクトリ構成
- `kyotei_predictor/data/raw/` : 生データ
- `kyotei_predictor/data/processed/` : 前処理済みデータ
- `outputs/feature_analysis/` : 分析出力

---

## 各スクリプトの使い方・引数例
- 詳細は各スクリプトのdocstring・README・docs/配下を参照

---

## 運用方針
- データ取得後、raw/→processed/への変換処理を担当
- AI学習・推論用のデータセット生成
- 新規パイプラインは本ディレクトリに追加
- 共通処理は tools/common/ へ集約

---

# 以下、従来の内容（構成・サンプルフロー等）は現状維持 