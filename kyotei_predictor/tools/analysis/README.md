# Analysis Tools

競艇データ分析ツール群です。オッズ分析・統計分析・モデル評価を担当します。

## 📁 ファイル構成

### 主要分析ツール
- `analyze_graduated_reward.py` - 段階的報酬モデルの分析・評価
- `analyze_reward_design.py` - 報酬設計の分析・最適化
- `analyze_state_vector.py` - 状態ベクトルの分析・可視化
- `feature_importance_analysis.py` - 特徴量重要度分析
- `investment_value_analyzer.py` - 投資価値分析・期待値計算
- `expected_value_threshold_optimizer.py` - 期待値閾値最適化

### データ検証・品質管理
- `bulk_prediction_validator.py` - 一括予測結果の検証
- `real_odds_investment_analyzer.py` - 実オッズ投資分析
- `verify_race_data.py` - レースデータ整合性チェック（詳細版・walk と集計）
- `verify_race_data_simple.py` - シンプルなレースデータ検証（軽量・単一ディレクトリ向け）
- `check_batch_results.py` - バッチ取得結果の検証
- `check_trifecta_hit_rate.py` - 3連単的中率チェック

### 統計・分析
- `odds_analysis.py` - オッズ分析（期待値計算・投資判定等）
- `race_stats.py` - レース統計分析
- `trifecta_probability_debugger.py` - 3連単確率デバッグ
- `racer_error_analyzer.py` - 選手エラー分析
- `simple_learning_test.py` - 学習テスト・検証

## 🚀 使用方法

### 主要分析
```bash
# 段階的報酬モデル分析
python tools/analysis/analyze_graduated_reward.py

# 特徴量重要度分析
python tools/analysis/feature_importance_analysis.py

# 投資価値分析
python tools/analysis/investment_value_analyzer.py

# 期待値閾値最適化
python tools/analysis/expected_value_threshold_optimizer.py
```

### データ検証
```bash
# レースデータの検証
python tools/analysis/verify_race_data.py data/raw/race_data_*.json

# シンプル検証
python tools/analysis/verify_race_data_simple.py data/raw/race_data_*.json

# バッチ取得結果の検証
python tools/analysis/check_batch_results.py data/raw/

# 3連単的中率チェック
python tools/analysis/check_trifecta_hit_rate.py
```

## 📊 分析機能

### モデル分析
- **段階的報酬設計**: 報酬関数の設計・最適化分析
- **状態ベクトル分析**: 192次元特徴量の分布・相関分析
- **特徴量重要度**: 機械学習モデルの特徴量重要度分析
- **学習曲線分析**: モデル学習の収束性・安定性評価

### 投資分析
- **期待値計算**: 3連単・3連複の期待値計算
- **投資価値判定**: 期待値ベースの投資判断
- **閾値最適化**: リスク・リターン最適化
- **戦略比較**: 複数投資戦略のパフォーマンス比較

### データ品質管理
- **整合性チェック**: レースデータの整合性・欠損チェック
- **バッチ結果検証**: 一括データ取得結果の検証
- **的中率分析**: 予測精度・的中率の統計分析
- **エラー分析**: データ取得・処理エラーの分析

### 統計分析
- **オッズ分析**: オッズ分布・統計分析・時系列変化
- **会場別分析**: 会場別・条件別の傾向分析
- **異常値検出**: 外れ値・異常値の検出・分析
- **相関分析**: 特徴量間の相関・依存関係分析

## 🔧 技術仕様

### 期待値計算
- **期待値 = オッズ × 的中確率**
- 的中確率はAI/強化学習モデルから取得
- 投資判定閾値の設定可能（0.8～2.0）

### 状態ベクトル
- **192次元特徴量**: 選手成績・機材情報・オッズ情報
- **正規化処理**: 標準化・正規化による前処理
- **欠損値処理**: 適切な欠損値補完・除外

### 出力形式
- **CSV/JSON**: 分析結果の構造化出力
- **可視化**: matplotlib/plotlyによるグラフ生成
- **レポート**: HTML/PDF形式でのレポート生成
- **ログ**: 詳細な実行ログ・エラーログ

## 📈 分析指標

### 投資指標
- **期待値**: 投資判断の基本指標
- **的中率**: 予測精度の評価
- **回収率**: 投資効率の測定
- **リスク指標**: シャープレシオ・最大ドローダウン

### 統計指標
- **記述統計**: 平均・分散・標準偏差
- **相関分析**: ピアソン・スピアマン相関係数
- **分布分析**: ヒストグラム・確率密度関数
- **時系列分析**: トレンド・季節性・周期性

### モデル評価指標
- **学習指標**: 損失関数・報酬関数の収束
- **汎化性能**: 過学習・アンダーフィッティングの検出
- **特徴量重要度**: モデル性能への寄与度
- **安定性**: 学習・予測の安定性評価

## 🎯 主要用途

### モデル開発・改善
- 報酬関数の設計・最適化
- 特徴量エンジニアリングの改善
- ハイパーパラメータの調整
- モデル性能の評価・比較

### 運用・監視
- データ品質の継続監視
- 予測精度の定期的評価
- 投資戦略の最適化
- システム性能の監視

### 研究・分析
- 競艇データの統計分析
- 機械学習モデルの研究
- 投資戦略の研究・開発
- データ駆動意思決定の支援 