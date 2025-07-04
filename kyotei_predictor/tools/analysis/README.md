# Analysis Tools

競艇データ分析ツール群です。オッズ分析・統計分析を担当します。

## 📁 ファイル構成

- `odds_analysis.py` - オッズ分析（期待値計算・投資判定等）

## 🚀 使用方法

### オッズ分析
```bash
python odds_analysis.py
```

## 📊 分析機能

### オッズ分析
- 3連単・3連複の期待値計算
- 投資価値判定（期待値ベース）
- オッズ分布・統計分析
- 組み合わせ別の的中率分析

### 統計分析
- オッズの時系列変化
- 会場別・条件別の傾向分析
- 異常値検出・外れ値分析

## 🔧 技術仕様

### 期待値計算
- **期待値 = オッズ × 的中確率**
- 的中確率はAI/強化学習モデルから取得
- 投資判定閾値の設定可能

### 出力形式
- CSV/JSON形式での分析結果出力
- 可視化チャート（matplotlib/plotly）
- レポート生成（HTML/PDF）

## 📈 分析指標

### 投資指標
- 期待値
- 回収率
- リスク指標（シャープレシオ等）
- 最大ドローダウン

### 統計指標
- 平均・分散・標準偏差
- 相関係数
- 分布分析

# analysis ディレクトリ

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- データ分析・検証ツール（オッズ分析、データ検証、バッチ結果チェック等）の役割・使い方・運用ルールを記載
- 主要スクリプトの説明・設計書へのリンクを明記
- ルートREADMEやtools/README、NEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../../README.md](../../../README.md)（全体概要・セットアップ・タスク入口）
- [../README.md](../README.md)（tools全体の運用ルール）
- [../../../NEXT_STEPS.md](../../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../../integration_design.md](../../../integration_design.md)（統合設計・アーキテクチャ）
- [../../../prediction_algorithm_design.md](../../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

## 役割・用途
- データの品質検証・分析・可視化
- オッズやバッチ結果の統計的分析
- データはdata/processed/やoutputs/に出力

---

## 主要スクリプト
- `odds_analysis.py` : オッズ分析
- `verify_race_data.py` : データ検証
- `check_batch_results.py` : バッチ結果チェック

---

## 運用ルール
- 入出力ファイルのパス・命名規則を統一
- 分析結果はoutputs/やresults/に保存
- 不要な一時ファイルは随時削除

---

# 以下、従来の内容（使い方・注意点など）を現状維持・必要に応じて最新化

## ファイル一覧

- odds_analysis.py
    - オッズデータの統計分析・可視化ツール
- verify_race_data.py
    - レースデータの整合性・欠損チェック、データ検証用スクリプト
- verify_race_data_simple.py
    - シンプルなレースデータ検証スクリプト（主に基本的な整合性チェック用）
- check_batch_results.py
    - バッチ取得結果の検証・集計・エラー検出用スクリプト

## 使い方

```bash
# レースデータの検証
python tools/analysis/verify_race_data.py data/raw/race_data_*.json

# シンプル検証
python tools/analysis/verify_race_data_simple.py data/raw/race_data_*.json

# バッチ取得結果の検証
python tools/analysis/check_batch_results.py data/raw/

# オッズ分析
python tools/analysis/odds_analysis.py data/raw/odds_data_*.json
```

## 備考
- データ検証・バッチ検証系のスクリプトはここに集約
- 分析・可視化系は `viz/` も参照 