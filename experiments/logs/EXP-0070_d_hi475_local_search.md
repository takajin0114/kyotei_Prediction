# EXP-0070: d_hi475 Local Search

## 実験目的

現行ベスト戦略（sigmoid calibration + d_hi475 + switch_dd4000）の周辺で、d_hi475 の EV 帯と prob 下限を局所探索し、ROI・total_profit・max_drawdown のバランス改善を狙う。

EXP-0065〜0069 により sigmoid 必須・d_hi475 有効・EV percentile / normalization / shrinkage は有効差なしまたは悪化と判明したため、今回は EV 帯・prob 下限のみを変えた局所探索を行う。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0070_d_hi475_local_search.py`
- **出力**: `outputs/d_hi475_local_search/exp0070_d_hi475_local_search.json`
- 既存 calib_sigmoid 予測（ev_cap_experiments/rolling_roi_predictions）を利用し、selection 条件のみ変更して評価。

## 共通条件

- calibration: sigmoid
- risk control: switch_dd4000
- rolling validation: n_windows=36
- skip_top20pct 適用済み（レース内 max_ev でソートし上位20%スキップ）

## 比較 CASE

| CASE | EV 帯            | prob 下限 | 備考        |
|------|------------------|-----------|-------------|
| CASE0 | 4.30 <= EV < 4.75 | 0.05      | baseline（現行 d_hi475） |
| CASE1 | 4.40 <= EV < 4.75 | 0.05      | EV 下限上げ |
| CASE2 | 4.50 <= EV < 4.75 | 0.05      | EV 下限さらに上げ |
| CASE3 | 4.30 <= EV < 4.70 | 0.05      | EV 上限下げ |
| CASE4 | 4.30 <= EV < 4.60 | 0.05      | EV 上限さらに下げ |
| CASE5 | 4.30 <= EV < 4.75 | 0.06      | prob 下限上げ |
| CASE6 | 4.40 <= EV < 4.70 | 0.06      | EV 帯絞り + prob 上げ |
| CASE7 | 4.50 <= EV < 4.70 | 0.06      | EV 帯絞り + prob 上げ |

## 実験結果（n_windows=36）

| variant | ev_lo | ev_hi | prob_min | ROI    | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-------|-------|----------|--------|--------------|--------------|----------------------|-----------|------------------------|
| CASE0   | 4.30  | 4.75  | 0.05     | 0.53%  | 484          | 15,886       | 469.45                | 1,031     | 4                     |
| CASE1   | 4.40  | 4.75  | 0.05     | 2.32%  | 1,654        | 14,394       | 2,039.46              | 811       | 14                    |
| CASE2   | 4.50  | 4.75  | 0.05     | **11.12%** | **5,772** | **8,838**   | **9,783.05**          | 590       | 9                     |
| CASE3   | 4.30  | 4.70  | 0.05     | 5.45%  | 4,410        | 12,866       | 4,819.67              | 915       | 4                     |
| CASE4   | 4.30  | 4.60  | 0.05     | -27.98%| -17,108      | 17,108       | -24,866.28            | 688       | 4                     |
| CASE5   | 4.30  | 4.75  | 0.06     | -13.58%| -11,666      | 13,266       | -12,002.06            | 972       | 4                     |
| CASE6   | 4.40  | 4.70  | 0.06     | -13.99%| -8,050       | 11,802       | -12,327.72            | 653       | 8                     |
| CASE7   | 4.50  | 4.70  | 0.06     | -12.18%| -4,732       | 11,482       | -10,730.16            | 441       | 10                    |

## 採用判断

- **CASE2（4.50 <= EV < 4.75, prob >= 0.05）**: ROI 11.12%、total_profit 5,772、max_drawdown 8,838 でいずれも baseline（CASE0）を上回る。profit_per_1000_bets も最大。**主軸候補として採用推奨（adopt）**。
- **CASE3（4.30 <= EV < 4.70, prob >= 0.05）**: ROI 5.45%、profit 4,410、longest_losing_streak 4 で baseline と同程度の連敗長。バランス型として **hold**・実運用のサブ候補。
- **CASE1**: ROI・profit は CASE0 より良いが longest_lose 14 と長い。攻め用オプションとして **hold**。
- **CASE4**: EV 上限 4.60 は切りすぎで大幅赤字。**reject**。
- **CASE5〜CASE7**: prob_min=0.06 はすべて baseline より悪化。**reject**。prob 下限は 0.05 維持を推奨。

## 考察

- EV 下限を 4.30 → 4.50 に上げる（CASE2）と、bet 数は減るが ROI・profit・max_dd が大きく改善。高 EV 帯に絞る効果が有効。
- EV 上限を 4.75 から下げると、4.70（CASE3）はまだ改善、4.60（CASE4）は過度な絞りで悪化。
- prob_min を 0.05 → 0.06 にすると全 CASE で悪化。現行 0.05 維持が妥当。
- 次の考察: CASE2 を実運用標準候補に格上げしたうえで、n_w=24/30 での頑健性確認や、CASE2 と CASE3 の 2 本立て（攻め・バランス）の検討が考えられる。
