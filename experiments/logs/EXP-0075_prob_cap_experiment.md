# EXP-0075: Probability Cap Experiment

## 実験目的

EXP-0074 の profit zone 分析で **prob ≥ 0.12 が大きな損失源**であることが確認された。主軸戦略（4.50 ≤ EV < 4.75, prob ≥ 0.05）に **prob 上限フィルタ**を追加し、ROI / total_profit / max_drawdown の改善があるかを検証する。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0075_prob_cap_experiment.py`
- **出力**: `outputs/prob_cap/exp0075_prob_cap.json`（outputs は gitignore のため**未コミット**）
- 既存 calib_sigmoid 予測（ev_cap_experiments/rolling_roi_predictions）を利用し、selection に prob 上限のみ追加して評価。

## 共通条件

- calibration: sigmoid
- risk_control: switch_dd4000
- rolling validation: n_windows=36
- skip_top20pct: true
- **ref_profit**: EXP-0070 と同一（4.30 ≤ EV < 4.75, prob ≥ 0.05）で算出した schedule を全 CASE 共通で使用

## 比較 CASE

| CASE | EV 帯            | prob 条件        | 備考           |
|------|------------------|-----------------|----------------|
| CASE0 | 4.50 ≤ EV < 4.75 | prob ≥ 0.05     | baseline（上限なし） |
| CASE1 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.12 | prob < 0.12 |
| CASE2 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.10 | prob < 0.10 |
| CASE3 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.09 | prob < 0.09 |
| CASE4 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.08 | prob < 0.08 |

## 実験結果（n_windows=36）

| variant | ev_lo | ev_hi | prob       | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-------|-------|------------|--------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0   | 4.50  | 4.75  | ≥0.05      | 11.12% | 5,772        | 8,838        | 9,783.05             | 590       | 9                     |
| CASE1   | 4.50  | 4.75  | 0.05–0.12  | 129.34%| 15,340       | 5,360        | 114,477.61           | 134       | 18                    |
| CASE2   | 4.50  | 4.75  | 0.05–0.10  | 132.42%| 13,110       | 4,500        | 117,053.57           | 112       | 18                    |
| CASE3   | 4.50  | 4.75  | 0.05–0.09  | **187.63%** | 15,010   | **3,980**     | **164,945.05**       | 91        | 12                    |
| CASE4   | 4.50  | 4.75  | 0.05–0.08  | 164.18%| 10,770       | 4,520        | 143,600.00           | 75        | 17                    |

## 採用判断

- **prob 上限フィルタは全 CASE で baseline（CASE0）を大きく上回る**。ROI・total_profit・max_drawdown・profit_per_1000_bets はいずれも改善。
- **CASE3（0.05 ≤ prob < 0.09）**: ROI 187.63%・total_profit 15,010・max_drawdown 3,980・longest_losing_streak 12 で、ROI・max_dd・profit/1k が最良。**主軸候補として採用推奨（adopt）**。
- **CASE1（prob < 0.12）**: total_profit 最大（15,340）だが longest_lose 18 と長い。攻め用オプションとして **hold**。
- **CASE4**: bet 数 75 と少なく、longest_lose 17。絞りすぎの可能性。**hold**。
- 結論: **prob 上限の導入を採用**。実運用候補は **CASE3（0.05 ≤ prob < 0.09）** を推奨。

## 考察

- EXP-0074 の「prob ≥ 0.12 が損失源」という知見と整合し、prob 上限を設けることで ROI・profit・max_dd が大きく改善した。
- 上限を厳しくする（0.12 → 0.10 → 0.09）と ROI は上昇するが、0.08（CASE4）では bet 数が減り total_profit は CASE3 より低下。0.09 がバランスの良い水準。
- longest_losing_streak は cap 導入で CASE1/CASE2 で 18 と伸びているが、CASE3 では 12 に短縮。サンプル数減少に伴うばらつきの可能性あり。n_w 変更での頑健性確認が次の検証候補。
