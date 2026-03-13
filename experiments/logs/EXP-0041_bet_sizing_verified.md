# Experiment: EXP-0041 ベットサイジング厳密検証

## experiment id

EXP-0041

## purpose

EXP-0040 では verify を 1 回だけ実行して payout を固定し、stake を後段で再計算していたため、ROI・total_profit が過大評価されている可能性がある。今回の目的は、各 sizing variant ごとに「selection → sizing → verify」を一体で実行し、bet 単位で stake と payout を対応させて、厳密な ROI / total_profit / max_drawdown を再評価すること。

## 固定条件（selection）

- skip_top20pct（日付内でレースを max_ev 降順に並べ、上位20%を除外）
- 3 ≤ EV < 5
- prob ≥ 0.05

（EXP-0038 採用条件のまま。selection 条件は変更しない。）

## sizing variant 定義

| variant | 式 |
|---------|---|
| baseline_fixed | unit = 100（全 bet 同額） |
| size_by_ev_linear | unit = clip(round(25×EV), 50, 200) |
| size_by_prob_linear | unit = clip(round(200×prob), 50, 200) |
| size_by_ev_prob | unit = clip(round(40×EV×prob), 50, 200) |
| size_by_ev_capped | unit = clip(round(25×EV), 50, 150) |
| size_by_ev_prob_capped | unit = clip(round(40×EV×prob), 50, 150) |

## payout / profit の厳密計算方法

- **odds の参照元**: `repo.get_odds(prediction_date, venue, rno)` で取得した odds_data の ratio（`get_odds_for_combination`）。
- **hit 判定**: 各 bet の combination が実際の着順（race_data から `get_actual_trifecta_from_race_data`）と一致すれば hit。
- **unit から stake への換算**: unit は円単位（50〜200）。stake = unit（そのまま）。
- **payout**: `payout_i = stake_i * odds_i`（hit 時のみ）。非 hit は 0。
- **profit**: `profit_i = payout_i - stake_i`。レース・window・全体で合算。
- **既存 verify_usecase**: 本実験では verify は使わず、race_data / odds_data を直接読み、bet 単位で hit / odds を取得し、各 variant の unit で stake と payout を算出。bet 単位で odds / hit / stake / payout の対応を完全に取っている。

## EXP-0040 との差分

- **EXP-0040**: verify を 1 回（confidence_weighted_ev_gap_v1）だけ実行し、race 単位の payout を取得。選ばれる bet 集合は全 variant で同一のため、各 variant で bet ごとの stake だけを再計算し、**同じ payout を流用**して `race_profit = payout - race_stake` を算出。このため「stake が小さい variant ほど ROI が高く出る」バイアスがあり、ROI・total_profit が過大評価されていた。
- **EXP-0041**: 各 bet ごとに stake（= unit）と hit/odds を対応させ、`payout_i = stake_i * odds_i`（hit 時）で払戻を計算。variant ごとに stake と payout が整合しており、厳密な ROI・total_profit となる。

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0041_bet_sizing_verified.py`
- 処理: 既存 rolling predictions を読み込み → skip_top20pct 適用 → 3≤EV<5 かつ prob≥0.05 の bet を抽出 → 各レースで repo から race_data / odds_data を取得し、bet 単位で (ev, prob, odds, hit) を構築 → 各 sizing variant で unit リストを算出 → 各 bet で stake = unit, payout = stake * odds if hit else 0 を計算 → window ごと・全体で集計。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0041_bet_sizing_verified \
  --db-path kyotei_predictor/data/kyotei_races.sqlite \
  --n-windows 18
```

## 結果表（n_windows=18）

| variant                  | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | hit_count | hit_rate | total_stake | avg_bet | avg_stake/race |
|--------------------------|---------|--------------|--------------|----------------------|-----------|-----------|----------|-------------|---------|----------------|
| baseline_fixed           | -4.39%  | -9,210       | 23,690       | -4,391.99            | 2,097     | 153       | 7.3%     | 209,700     | 100.0   | 102.69        |
| size_by_ev_linear        | -4.61%  | -9,326       | 25,012       | -4,447.40            | 2,097     | 153       | 7.3%     | 202,116     | 96.38   | 98.98         |
| size_by_prob_linear      | -11.68% | -19,774     | 24,088       | -9,429.52            | 2,097     | 153       | 7.3%     | 169,365     | 80.77   | 82.94         |
| size_by_ev_prob          | -9.90%  | -14,582     | 19,515       | -6,953.70            | 2,097     | 153       | 7.3%     | 147,326     | 70.26   | 72.15         |
| size_by_ev_capped        | -4.61%  | -9,326       | 25,012       | -4,447.40            | 2,097     | 153       | 7.3%     | 202,116     | 96.38   | 98.98         |
| size_by_ev_prob_capped   | -9.56%  | -13,889     | 18,889       | -6,623.22            | 2,097     | 153       | 7.3%     | 145,258     | 69.27   | 71.14         |

## EXP-0040 との数値差

| variant                  | EXP-0040 ROI | EXP-0041 ROI | EXP-0040 total_profit | EXP-0041 total_profit |
|--------------------------|--------------|--------------|------------------------|------------------------|
| baseline_fixed           | +77.19%      | -4.39%       | +161,865               | -9,210                 |
| size_by_ev_prob_capped   | +155.80%     | -9.56%       | +226,307               | -13,889                |

EXP-0040 は「同一 payout を stake だけ変えて再計算」していたため、stake が小さい variant ほど ROI が極端に高く出ていた。厳密に bet 単位で payout = stake × odds を計算すると、全 variant で赤字となり、EXP-0040 の数値は参考値に過ぎない。

## 解釈

1. **厳密計算では全 variant が赤字**  
   selection 条件（skip_top20pct + 3≤EV<5 + prob≥0.05）を固定した上で、stake と payout を bet 単位で整合させると、いずれの sizing でも ROI はマイナスである。EXP-0040 で得られた高 ROI は、payout の流用による計算上のバイアスであった。

2. **相対的な優劣**  
   厳密計算でも、baseline_fixed（ROI -4.39%）や size_by_ev_linear / size_by_ev_capped（-4.61%）が、size_by_prob_linear（-11.68%）や size_by_ev_prob / size_by_ev_prob_capped（-9.56〜-9.90%）よりマシである。EV 比例や同額に近い sizing の方が、同じ bet 集合では損失が小さい。

3. **max_drawdown**  
   size_by_ev_prob_capped が 18,889 で最小。stake を抑えているため変動は小さいが、利益は出ていない。

4. **採用判断の前提**  
   今回の実験を「正」とする。EXP-0040 の adopt 判断（size_by_ev_prob_capped 採用）は、計算方法の違いにより過大評価に基づいており、実運用の「黒字化」根拠としては使わない。

## 採用判断

- **EXP-0041 を正とする**。EXP-0040 より数値は悪化しているが、計算として正しいのは EXP-0041 である。
- **ベットサイジングの公式採用**: 厳密評価では全 variant が赤字のため、「どれを採用すれば黒字になる」という採用は行わない。実運用では selection 条件（skip_top20pct + 3≤EV<5 + prob≥0.05）を維持しつつ、sizing は **baseline_fixed（unit=100）** または **size_by_ev_linear / size_by_ev_capped** のように相対的に損失が小さいものを「参考」とする。EXP-0040 で adopt した size_by_ev_prob_capped は、厳密計算では赤字であり、過大評価であったことを明記する。
- **ドキュメント**: leaderboard・chat_context・project_status では、EXP-0040 は「後段 sizing による参考値」、EXP-0041 を「厳密再検証の正」として記載する。

## 結果 JSON

outputs/bet_sizing_optimization/exp0041_bet_sizing_verified_results.json
