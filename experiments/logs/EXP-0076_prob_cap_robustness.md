# EXP-0076: Probability Cap Robustness Check

## 実験目的

EXP-0075 で probability cap が有効である可能性が確認されたが、bet_count が少なく ROI が極端に高いため、**頑健性（robustness）**を検証する。rolling window horizon（n_windows = 24 / 30 / 36）を変えて比較し、結果の再現性を確認する。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0076_prob_cap_robustness.py`
- **出力**: `outputs/prob_cap_robustness/exp0076_prob_cap_robustness.json`（outputs は gitignore のため**未コミット**）
- 既存 calib_sigmoid 予測（ev_cap_experiments/rolling_roi_predictions）を利用し、CASE0〜CASE3 × n_windows 24/30/36 で評価。

## 共通条件

- calibration: sigmoid
- risk_control: switch_dd4000
- skip_top20pct: true
- **ref_profit**: EXP-0070 と同一（4.30 ≤ EV < 4.75, prob ≥ 0.05）で算出した schedule を全 CASE・全 horizon 共通で使用

## 比較 CASE

| CASE | EV 帯            | prob 条件        | 備考           |
|------|------------------|-----------------|----------------|
| CASE0 | 4.50 ≤ EV < 4.75 | prob ≥ 0.05     | baseline（上限なし） |
| CASE1 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.12 | prob < 0.12 |
| CASE2 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.10 | prob < 0.10 |
| CASE3 | 4.50 ≤ EV < 4.75 | 0.05 ≤ prob < 0.09 | prob < 0.09 |

## 実験結果

### n_windows = 24

| variant | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak | block_profit |
|---------|--------|--------------|--------------|----------------------|-----------|------------------------|--------------|
| CASE0   | 30.10% | 11,036       | 6,698        | 27,452.74            | 402       | 7                      | [6398, -1644, -3352, 5970, 5258, -1594] |
| CASE1   | 219.25%| 18,680       | 3,180       | 200,860.22           | 93        | 11                     | [6890, -740, -1040, 10690, 4000, -1120] |
| CASE2   | 225.92%| 15,950       | 2,540       | 207,142.86           | 77        | 11                     | [7470, -740, -880, 6700, 4260, -860] |
| CASE3   | 319.89%| 17,530       | 1,860       | 292,166.67           | 60        | 6                      | [8150, -580, -640, 6900, 4560, -860] |

### n_windows = 30

| variant | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak | block_profit |
|---------|--------|--------------|--------------|----------------------|-----------|------------------------|--------------|
| CASE0   | 15.34% | 6,908        | 6,698        | 13,706.35            | 504       | 7                      | [7138, -3728, 1672, 7548, -874, -4848] |
| CASE1   | 155.16%| 16,540       | 4,160       | 138,991.60           | 119       | 12                     | [6790, -1280, 6700, 7590, -1420, -1840] |
| CASE2   | 157.38%| 14,070       | 3,540       | 140,700.00           | 100       | 12                     | [7370, -1200, 6880, 3760, -1060, -1680] |
| CASE3   | 223.17%| 15,890       | 3,100       | 198,625.00           | 80        | 12                     | [8050, -960, 7140, 4160, -1060, -1440] |

### n_windows = 36

| variant | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak | block_profit |
|---------|--------|--------------|--------------|----------------------|-----------|------------------------|--------------|
| CASE0   | 11.12% | 5,772        | 8,838        | 9,783.05             | 590       | 9                      | [5698, -4296, 11398, -1764, -4128, -1136] |
| CASE1   | 129.34%| 15,340       | 5,360       | 114,477.61           | 134       | 18                     | [6470, -1360, 15590, -2020, -2140, -1200] |
| CASE2   | 132.42%| 13,110       | 4,500       | 117,053.57           | 112       | 18                     | [7050, -1200, 11760, -1660, -1880, -960] |
| CASE3   | 187.63%| 15,010       | 3,980       | 164,945.05           | 91        | 12                     | [7730, -800, 12060, -1460, -1640, -880] |

## 採用判断

- **全 horizon（24/30/36）で prob cap CASE（CASE1〜CASE3）が baseline（CASE0）を一貫して上回る**。ROI・total_profit・max_drawdown・profit_per_1000_bets はいずれの n_windows でも cap 導入が有利。
- **CASE3（0.05 ≤ prob < 0.09）**: 全 horizon で ROI が最良（24: 319.89%, 30: 223.17%, 36: 187.63%）。max_drawdown も各 horizon で最小または最小クラス。**probability cap の頑健性は確認された。実運用候補は CASE3 維持で adopt**。
- **horizon 依存**: n_w が短い（24）ほど ROI は高く出るが bet_count はさらに減少。n_w=36 でも CASE3 は ROI 187.63%・profit 15,010・max_dd 3,980 と EXP-0075 と整合。再現性あり。
- **block_profit**: 全 CASE で後半ブロック（5〜6 ブロック目）は負けが多く、EXP-0051 の後半悪化傾向と整合。cap CASE でも同様の regime は存在するが、baseline より絶対値は小さい。

## 考察

- EXP-0075 の「prob 上限が有効」という結論は、n_windows 24/30/36 のいずれでも再現した。**probability cap は horizon に依存せず頑健**。
- bet_count は cap を厳しくするほど減少（CASE3 で n_w=36 でも 91）。ROI が極端に高い要因の一つはサンプル数が少ないことだが、複数 horizon で一貫して cap が baseline を上回るため、**採用判断は維持**。
- 次の考察: 実運用では n_w=36 を基準に CASE3 を主軸とし、block 単位のモニタリング（後半ブロックの負け傾向）を継続することが妥当。
