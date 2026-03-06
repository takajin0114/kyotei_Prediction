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

## 複数日 A/B 実験（条件統一・2024-07-01〜07）

### 条件（完全統一）

- **betting_strategy**: top_n
- **top_n**: 3
- **evaluation_mode**: selected_bets
- **data_dir**: kyotei_predictor/data/raw/2024-07
- **date**: 2024-07-01 〜 2024-07-07（複数会場: EDOGAWA, KIRYU, TODA）

### 集計結果

| 項目 | A案（PPO） | B案（Baseline） |
|------|------------|----------------|
| **ROI** | 14.8% | 982.98% |
| **hit_rate (1位)** | 21.97% | 73.48% |
| **hit_rate (top3)** | 25.2% | 72.22% |
| **total_bet** | 39600 | 39600 |
| **total_payout** | 45460 | 428860 |
| **hit_count** | 29 | 97 |
| **races_with_result** | 132 | 132 |

### 保存先

- **logs/ab_test_multi_day.json**（日別結果 + 集計）
- 外し傾向の集計: **docs/ab_error_analysis.md**（会場別・枠番別・オッズ帯別）

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
| **ROI** | 14.8% | 982.98% |
| **hit_rate (1位)** | 21.97% | 73.48% |
| **hit_rate (top3)** | 25.2% | 72.22% |
| **betting_strategy** | top_n | top_n |
| **evaluation_mode** | selected_bets | selected_bets |

（2024-07-01〜07・132R・条件統一: top_n=3, selected_bets）

### Error Analysis

- **会場**: EDOGAWA で A の外し 57、B の外し 21。KIRYU で A 29・B 9。TODA で A 17・B 5。B案は全会場で外しが少ない。
- **枠番**: 1着が 1 号艇のレースで A は 44 外し、B は 0 外し。本命 1 号艇のときに A が外しやすい傾向。
- **人気**: オッズ帯では 10-50 のレースで A 50 外し・B 15 外し。詳細は **docs/ab_error_analysis.md** を参照。

### Next Steps

1. **モデル改善**: A案（PPO）の 1 号艇本命時の外しを減らす（報酬設計・特徴量の見直し）。B案は特徴量拡張（`docs/B_BASELINE_IMPROVEMENT.md`）でさらに安定化。
2. **EV 戦略**: オッズ接続と expected_value 計算（`docs/EV_STRATEGY_ROADMAP.md`）を本格化し、top_n に加えて EV 閾値でも比較する。
3. **人気順位集計**: オッズ順位での外し傾向（本命・対抗・単穴）を別集計し、ab_error_analysis に追記する。
