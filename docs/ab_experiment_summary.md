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

## 実データ実験（2024-07-04・EDOGAWA 12R）

### 条件

- **date**: 2024-07-04
- **data_dir**: kyotei_predictor/data/raw/2024-07
- **betting_strategy**: top_n（推奨設定）
- **evaluation_mode**: selected_bets
- **top_n**: 3（B案は CLI で明示指定。A案は improvement_config に依存）

### 結果

| 項目 | A案（PPO） | B案（Baseline） |
|------|------------|----------------|
| **ROI** | 0.0% | 1028.89% |
| **hit_rate (1位)** | 0.0% | 58.33% |
| **hit_rate (top3)** | 25.0% | 58.33% |
| **betting_strategy** | selected_bets | top_n |
| **evaluation_mode** | selected_bets | selected_bets |
| **total_bet** | 1200 | 3600 |
| **total_payout** | 0 | 37040 |
| **hit_count** | 0 | 7 |
| **races_with_result** | 12 | 12 |

### 保存先

- **logs/ab_test_result_20250306.json**（実験日 2025-03-06 実行分）
- 含む指標: roi_pct, hit_rate_rank1_pct（hit_rate_1）, hit_rate_top3_pct, total_bet, total_payout, hit_count

---

## 実行例（テストデータ・参考）

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

※ オッズデータなしのため total_payout=0。

### 比較結果の保存先

- `logs/ab_test_result_YYYYMMDD.json` または `logs/ab_test_result_YYYYMMDD.csv`
- 実行例:  
  `python -m kyotei_predictor.cli.compare_ab --prediction-a <A案JSON> --prediction-b <B案JSON> --data-dir <data_dir> --evaluation-mode selected_bets --output logs/ab_test_result_20250306.json`

---

## 観察ポイント

- **B案がどこで外しているか**: レース別の詳細（verify の details）で、B案が 1 位を外したレースの傾向（会場・枠番・展示タイム等）を確認する。
- **hit_rate と ROI の関係**: 1位的中率が高くてもオッズ次第で ROI は変動する。selected_bets で買い目数を増やした場合は total_bet が増え、ROI の解釈が変わる。
- **selected_bets の件数**: strategy=top_n の N や threshold の閾値で、レースあたりの買い目数が変わる。多すぎると total_bet が膨らみ、少なすぎると取りこぼしが増える。

---

## 外し傾向メモ（2024-07-04 実データ）

- **どの会場で外すか**: 今回の対象は **EDOGAWA のみ**（12レース）。会場別の外し傾向を見るには、複数会場・複数日の結果を積み重ねる必要がある。
- **どの枠番で外すか**: レース別の verify details（1着予想の枠番 vs 実際の1着枠番）を集計すると、特定枠番で外しやすいかが分かる。未集計の場合は `verify_predictions` の詳細出力を参照。
- **人気サイドか穴サイドか**: 1位予想が本命・対抗寄りか、穴寄りかをオッズと照合すると、人気に振れているか穴に振れているかの傾向が分かる。今回 B案は 7/12 で1位的中・ROI 1028% のため、この日は人気～中穴で当たっている可能性がある。
- **A案（PPO）の外し**: 今回 A案は 1位 0 的中（hit_count=0）。12レースすべてで 1 位を外しており、この日・この会場では PPO の 1 位予想が実着と合わなかった。3位以内は 25% のため、2～3着には一部入っている。

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

### Experiment Result

| 項目 | A案（PPO） | B案（Baseline） |
|------|------------|----------------|
| **ROI** | 0.0% | 1028.89% |
| **hit_rate (1位)** | 0.0% | 58.33% |
| **hit_rate (top3)** | 25.0% | 58.33% |
| **betting_strategy** | selected_bets | top_n |
| **evaluation_mode** | selected_bets | selected_bets |

（実データ 2024-07-04・EDOGAWA 12R、top_n=3・selected_bets で検証）

### Observation

- **どちらが良かったか**: 今回の1日では **B案（Baseline）が有利**。ROI・1位的中率・的中数とも B案が上。
- **なぜそうなったか**: A案（PPO）はこの日 1位 0 的中で、選んだ買い目に本命が含まれていなかった可能性がある。B案は同じ状態ベクトルベースの教師あり分類で、2024-07 の着順データで学習しており、この日の傾向に合いやすかった可能性がある。1日のみのため、複数日・複会場で再実験すると傾向が安定する。

### Improvement Candidates

- **特徴量**: `docs/B_BASELINE_IMPROVEMENT.md` の拡張候補（モーター・ボート勝率、展示タイム、スタート、枠番補正など）を順次検証する。
- **EV戦略**: `docs/EV_STRATEGY_ROADMAP.md` に沿い、オッズ接続と expected_value 計算を本格化する。

### Next Steps

1. 複数日・複会場で A/B を再実行し、外し傾向（会場・枠番・人気/穴）を集計する。
2. B案の特徴量拡張を1つ選び実装し、同じ条件で A/B を再比較する。
3. A案（PPO）の買い目選定（top_n や閾値）を improvement_config で B案と揃え、同条件で再実験する。
