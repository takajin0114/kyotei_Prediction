# A/B 実験サマリ

実データ（またはテストデータ）で A案・B案を同一条件で比較した結果を整理する。

---

## 実験条件の揃え方

以下を必ず揃えること。

| 項目 | 説明 |
|------|------|
| **date** | 予測日（同一日） |
| **data_dir** | 同じ race_data / odds_data のディレクトリ |
| **betting_strategy** | single / top_n / threshold / ev のいずれかで統一 |
| **evaluation_mode** | first_only または selected_bets で統一 |
| **top_n / threshold / ev_threshold** | strategy に応じたパラメータを統一 |

---

## 取得指標

- **roi_pct**: 回収率（%）
- **hit_rate**: 1位的中率（hit_rate_rank1_pct）、3位以内的中率（hit_rate_top3_pct）
- **total_bet**: 総購入額（円）
- **total_payout**: 総払戻額（円）
- **hit_count**: 的中数

---

## 実行例（2025-03-06 テストデータでの1回実行）

### 条件

- **date**: 2024-05-01
- **data_dir**: /tmp/ab_test_data（3レース・着順入り）
- **betting_strategy**: first_only
- **evaluation_mode**: first_only

### 結果

| 項目 | A案（PPO） | B案（Baseline） |
|------|------------|----------------|
| **ROI** | 0.0% | 0.0% |
| **hit_rate (1位)** | 100.0% | 100.0% |
| **hit_rate (top3)** | 100.0% | 100.0% |
| **total_bet** | 300 | 300 |
| **total_payout** | 0 | 0 |
| **hit_count** | 3 | 3 |

※ 本実行はオッズデータなしのため total_payout=0、roi_pct=0%。実データで odds_data を揃えれば払戻・ROI が算出される。

### 比較結果の保存先

- `logs/ab_test_result_YYYYMMDD.json` または `logs/ab_test_result_YYYYMMDD.csv`
- 実行例:  
  `python -m kyotei_predictor.cli.compare_ab --prediction-a <A案JSON> --prediction-b <B案JSON> --data-dir <data_dir> --output logs/ab_test_result_20250306.json`

---

## 観察ポイント

- **B案がどこで外しているか**: レース別の詳細（verify の details）で、B案が 1 位を外したレースの傾向（会場・枠番・展示タイム等）を確認する。
- **hit_rate と ROI の関係**: 1位的中率が高くてもオッズ次第で ROI は変動する。selected_bets で買い目数を増やした場合は total_bet が増え、ROI の解釈が変わる。
- **selected_bets の件数**: strategy=top_n の N や threshold の閾値で、レースあたりの買い目数が変わる。多すぎると total_bet が膨らみ、少なすぎると取りこぼしが増える。

---

## 実データで A/B を1回実行する手順

1. **A案予測**:  
   `python -m kyotei_predictor.cli.predict --predict-date YYYY-MM-DD`（または prediction_tool）で A案の予測 JSON を出力する。
2. **B案予測**:  
   `python -m kyotei_predictor.cli.baseline_predict --predict-date YYYY-MM-DD --data-dir <data_dir> [--include-selected-bets --strategy top_n --top-n 3]` で B案の予測 JSON を出力する。
3. **比較**:  
   `python -m kyotei_predictor.cli.compare_ab --prediction-a <A案JSON> --prediction-b <B案JSON> --data-dir <data_dir> --evaluation-mode first_only --output logs/ab_test_result_YYYYMMDD.json`
4. 結果をこのドキュメントの「結果」表に追記し、観察ポイントをメモする。

---

## 最終出力（Sprint サマリ用）

### Experiment Summary

| 項目 | A案（PPO） | B案（Baseline） |
|------|------------|----------------|
| **ROI** | （実データ実行時に記入） | （実データ実行時に記入） |
| **hit_rate (1位)** | （同上） | （同上） |
| **hit_rate (top3)** | （同上） | （同上） |

※ 上記は実データで A/B を実行したあと、結果を貼り替える。

### Observation

- **どちらが良かったか**: 同一条件で roi_pct と hit_rate を比較し、どちらが高いかを記録する。
- **なぜそうなったか**: モデルの違い（強化学習 vs 教師あり分類）、学習データ量・質、特徴量の差、買い目数（selected_bets 時）の差などをメモする。

### Improvement Candidates

B案の改善候補は `docs/B_BASELINE_IMPROVEMENT.md` に整理した。

- 特徴量拡張（モーター・ボート勝率、展示タイム、スタート、枠番補正など）
- 順位確率モデル（P(1着) / P(2着) / P(3着) の分離）

### Next Steps

1. 実データ（同一日・同一 data_dir）で A案・B案の予測を取得し、compare_ab で ROI / hit_rate を比較する。
2. B案の改善候補から優先度の高い特徴量拡張を1つ選び、最小限実装して A/B を再実行する。
3. EV 戦略の本格化準備として、オッズ接続と expected_value 計算を `docs/EV_STRATEGY_ROADMAP.md` に沿って進める。
