# 3連単確率計算のテスト実行・改善計画

**作成日**: 2025-07-06  
**最終更新日**: 2025-07-06  
**対象**: `kyotei_predictor/pipelines/trifecta_probability.py`  
**関連ファイル**: `kyotei_predictor/tests/ai/test_trifecta_probability.py`

---

## 📋 概要

競艇予測システムにおける3連単確率計算機能の現状テスト・改善・最適化を実施する。既存実装の精度向上と新機能追加により、より実用的な投資判断支援システムを構築する。

### 現在の実装状況
- ✅ `TrifectaProbabilityCalculator`クラス実装済み
- ✅ 基本確率計算ロジック実装済み
- ✅ 投資価値分析機能実装済み
- ✅ テストスイート実装済み
- ⚠️ 精度検証・最適化が必要
- ⚠️ 新機能追加が必要

---

## 🎯 Phase 1: 現状テスト実行・問題特定 ⭐ **最優先**

### 1.1 基本テスト実行
- [ ] **仮想環境有効化・テスト実行**
  ```bash
  venv311\Scripts\activate
  $env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tests/ai/test_trifecta_probability.py
  ```
- [ ] **テスト結果の分析・問題点特定**
  - エラー・警告の確認
  - 期待値と実際値の乖離分析
  - パフォーマンス問題の特定
  - メモリ使用量の確認

### 1.2 サンプルデータでの検証
- [ ] **サンプルデータの品質確認**
  - `data/sample/`のデータ構造確認
  - レースデータとオッズデータの整合性チェック
  - 欠損値・異常値の検出
- [ ] **複数レースでの検証**
  - 桐生R1-R12の全レースでテスト実行
  - 予測精度の統計分析
  - 的中率の測定

### 1.3 問題点の文書化
- [ ] **発見された問題の整理**
  - バグ・エラーの詳細記録
  - 精度不足の原因分析
  - パフォーマンスボトルネックの特定
- [ ] **改善優先度の決定**
  - 影響度・緊急度による優先順位付け
  - 実装難易度の評価

---

## 🔧 Phase 2: アルゴリズム改善・最適化 ⭐ **高優先**

### 2.1 重み調整・パラメータ最適化
- [ ] **重みパラメータの最適化**
  ```python
  # 現在のDEFAULT_WEIGHTS
  DEFAULT_WEIGHTS = {
      'all_stadium_rate': 0.35,      # 全国勝率
      'event_going_rate': 0.25,      # 当地勝率
      'rating': 0.1,                 # 級別補正
      'boat_quinella_rate': 0.15,    # ボート2連率
      'motor_quinella_rate': 0.15,   # モーター2連率
      'course_bias': 0.0,            # コース特性（拡張）
      'odds_bias': 0.0,              # オッズ補正（拡張）
  }
  ```
  - 選手成績 vs 機材成績の最適比率検討
  - 級別補正の効果検証
  - コース特性・オッズ補正の重み調整

- [ ] **2着・3着重みの調整**
  ```python
  # 現在の設定
  second_weight: float = 0.8  # 2着艇の確率重み
  third_weight: float = 0.6   # 3着艇の確率重み
  ```
  - 実際の着順データとの照合
  - 最適な重み値の導出

### 2.2 確率計算ロジックの改善
- [ ] **独立性仮定の見直し**
  - 選手間の相関関係考慮
  - コース特性の影響分析
  - 機材・選手の相性分析
- [ ] **正規化手法の改善**
  ```python
  # 現在の正規化
  norm_scores = [((s - min_score) / (max_score - min_score) if max_score > min_score else 1.0) for s in scores]
  ```
  - スコア正規化の方法見直し
  - 異常値処理の改善
  - より安定した正規化手法の導入

### 2.3 期待値計算の改善
- [ ] **より精密な期待値計算**
  ```python
  @staticmethod
  def calc_expected_value(probability: float, odds: float) -> float:
      return probability * odds
  ```
  - リスク調整後の期待値
  - 分散・標準偏差の考慮
  - 信頼区間の計算

---

## 🚀 Phase 3: 新機能追加・拡張 ⭐ **中優先**

### 3.1 コース特性・環境要因の統合
- [ ] **コース特性データの統合**
  ```python
  # 追加予定の特徴量
  'course_bias': 0.15,        # コース別成績の重み付け
  'wind_effect': 0.05,        # 風向・風速の影響
  'wave_effect': 0.05,        # 波高の影響
  'time_bias': 0.05,          # 時間帯による変動
  ```
  - コース別成績の重み付け
  - 風向・波高の影響分析
  - 時間帯による変動考慮

- [ ] **環境要因の考慮**
  - 天候・気温の影響
  - 季節補正
  - 開催回数による調整

### 3.2 投資価値分析の強化
- [ ] **ポートフォリオ分析**
  ```python
  def analyze_portfolio(combinations: list, budget: float) -> dict:
      """複数組み合わせの最適化"""
      pass
  ```
  - 複数組み合わせの最適化
  - 資金配分の推奨
  - リスク分散の考慮

- [ ] **リスク管理機能**
  - 最大損失の制限
  - 期待値の信頼区間
  - ストップロス機能

### 3.3 機械学習統合
- [ ] **特徴量エンジニアリング**
  - 非線形特徴量の追加
  - 特徴量選択の自動化
  - 特徴量重要度の分析
- [ ] **モデル最適化**
  - Optunaによるハイパーパラメータ最適化
  - クロスバリデーション
  - アンサンブル手法の導入

---

## 🧪 Phase 4: テスト・検証の強化 ⭐ **中優先**

### 4.1 包括的テストスイート
- [ ] **ユニットテストの拡充**
  ```python
  def test_score_calculation():
      """スコア計算のテスト"""
      pass
  
  def test_probability_normalization():
      """確率正規化のテスト"""
      pass
  
  def test_edge_cases():
      """エッジケースのテスト"""
      pass
  ```
  - 各メソッドの個別テスト
  - エッジケースのテスト
  - 異常値処理のテスト

- [ ] **統合テストの実装**
  - エンドツーエンドテスト
  - パフォーマンステスト
  - メモリリークテスト

### 4.2 精度評価・ベンチマーク
- [ ] **予測精度の定量評価**
  ```python
  def calculate_accuracy_metrics(predictions: list, actual_results: list) -> dict:
      """精度指標の計算"""
      return {
          'hit_rate': 0.0,           # 的中率
          'expected_value': 0.0,     # 期待値
          'profit_loss': 0.0,        # 損益
          'sharpe_ratio': 0.0,       # シャープレシオ
      }
  ```
  - 的中率の測定
  - 期待値の実現率
  - シャープレシオの計算

- [ ] **他アルゴリズムとの比較**
  - ベースラインとの比較
  - 改善効果の定量化
  - A/Bテストの実施

### 4.3 バックテスト機能
- [ ] **履歴データでの検証**
  ```python
  def backtest_strategy(historical_data: list, strategy: dict) -> dict:
      """バックテスト実行"""
      pass
  ```
  - 過去データでの戦略検証
  - 期間別パフォーマンス分析
  - ドローダウンの測定

---

## 📚 Phase 5: ドキュメント・運用改善 ⭐ **低優先**

### 5.1 ドキュメント整備
- [ ] **API仕様書の更新**
  ```markdown
  ## TrifectaProbabilityCalculator
  
  ### 使用方法
  ```python
  calculator = TrifectaProbabilityCalculator(
      second_weight=0.8,
      third_weight=0.6,
      weights=custom_weights
  )
  results = calculator.calculate(predictions)
  ```
  
  ### パラメータ説明
  - `second_weight`: 2着艇の確率重み（0.0-1.0）
  - `third_weight`: 3着艇の確率重み（0.0-1.0）
  - `weights`: 特徴量ごとの重み辞書
  ```
  - 使用方法の詳細化
  - パラメータ説明の充実
  - トラブルシューティング

- [ ] **ベストプラクティス**
  - 推奨設定値の明記
  - パフォーマンスチューニング
  - 運用上の注意点

### 5.2 運用改善
- [ ] **ログ・モニタリング**
  ```python
  def log_prediction_accuracy(prediction: dict, actual_result: str):
      """予測精度のログ記録"""
      pass
  ```
  - 予測精度の自動記録
  - 異常値の自動検出
  - パフォーマンス監視

- [ ] **設定管理**
  ```python
  # config/trifecta_config.json
  {
      "default_weights": {...},
      "optimization_params": {...},
      "logging_config": {...}
  }
  ```
  - 設定ファイル化
  - 環境別設定の管理
  - 設定変更の履歴管理

---

## 📊 成功指標・KPI

### 精度指標
- **的中率**: 目標 15%以上（上位10位以内）
- **期待値**: 目標 1.1以上
- **シャープレシオ**: 目標 0.5以上

### パフォーマンス指標
- **計算時間**: 1レースあたり 1秒以内
- **メモリ使用量**: 100MB以内
- **スループット**: 100レース/分以上

### 運用指標
- **テストカバレッジ**: 90%以上
- **ドキュメント完成度**: 100%
- **バグ発生率**: 月1件以下

---

## 🗓️ スケジュール

### Week 1: Phase 1
- 現状テスト実行
- 問題点特定
- 改善計画策定

### Week 2-3: Phase 2
- アルゴリズム改善
- パラメータ最適化
- 基本機能強化

### Week 4-5: Phase 3
- 新機能追加
- コース特性統合
- 投資価値分析強化

### Week 6: Phase 4
- テスト強化
- 精度評価
- バックテスト

### Week 7: Phase 5
- ドキュメント整備
- 運用改善
- 最終検証

---

## 🔗 関連ドキュメント

- [prediction_algorithm_design.md](../../../prediction_algorithm_design.md)
- [NEXT_STEPS.md](../../../NEXT_STEPS.md)
- [integration_design.md](../../../integration_design.md)
- [test_trifecta_probability.py](test_trifecta_probability.py)
- [trifecta_probability.py](../../pipelines/trifecta_probability.py)

---

## 📝 進捗管理

### 進捗記録
- [ ] Phase 1 完了
- [ ] Phase 2 完了
- [ ] Phase 3 完了
- [ ] Phase 4 完了
- [ ] Phase 5 完了

### 課題管理
- [ ] 課題1: [課題内容]
- [ ] 課題2: [課題内容]
- [ ] 課題3: [課題内容]

### 次回更新予定
- **次回更新日**: 2025-07-13
- **更新内容**: Phase 1の結果報告 