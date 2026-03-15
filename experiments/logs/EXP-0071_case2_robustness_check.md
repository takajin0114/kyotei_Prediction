# EXP-0071: CASE2 Robustness Check

## 実験目的

EXP-0070 で採用した CASE2（4.50 ≤ EV < 4.75, prob ≥ 0.05）が **n_windows に依存しないか** を確認する。局所探索ではなく **CASE2 の再現性・頑健性** を評価する。

## 実装内容

- **ツール**: `kyotei_predictor/tools/run_exp0071_case2_robustness_check.py`
- **出力**: `outputs/case2_robustness/exp0071_case2_robustness.json`（outputs は gitignore のため未コミット）
- EXP-0070 と同一の selection・stake 計算・rolling 参照（calib_sigmoid rolling prediction）を踏襲。

## 比較 CASE

| CASE | EV 帯 | prob 下限 | 備考 |
|------|--------|-----------|------|
| CASE0 | 4.30 ≤ EV < 4.75 | 0.05 | baseline d_hi475 |
| CASE2 | 4.50 ≤ EV < 4.75 | 0.05 | EXP-0070 採用戦略 |
| CASE3 | 4.30 ≤ EV < 4.70 | 0.05 | バランス型 |

## 比較 horizon

- n_windows: **24, 30, 36**

## 実験条件

- calibration: sigmoid
- risk control: switch_dd4000
- skip_top20pct: 適用（EXP-0070 と同一）
- switch_dd4000 の stake スケジュール: CASE0 の ref_profit で算出し、全 CASE で共通使用
- 予測: 既存 `outputs/ev_cap_experiments/rolling_roi_predictions`（calib_sigmoid）を使用

## 実験結果

| variant | n_w | ROI | total_profit | max_drawdown | profit_per_1000_bets | bet_count | longest_losing_streak |
|---------|-----|-----|--------------|--------------|----------------------|-----------|------------------------|
| CASE0 | 24 | 18.24% | 11,744 | 7,766 | 16,681.82 | 704 | 4 |
| CASE2 | 24 | **30.10%** | 11,036 | **6,698** | **27,452.74** | 402 | 7 |
| CASE3 | 24 | 23.22% | **13,386** | 7,730 | 21,247.62 | 630 | 4 |
| CASE0 | 30 | 6.04% | 4,796 | 10,702 | 5,419.21 | 885 | 4 |
| CASE2 | 30 | **15.34%** | 6,908 | **6,698** | **13,706.35** | 504 | 7 |
| CASE3 | 30 | 10.30% | **7,282** | 9,122 | 9,252.86 | 787 | 4 |
| CASE0 | 36 | 0.53% | 484 | 15,886 | 469.45 | 1,031 | 4 |
| CASE2 | 36 | **11.12%** | **5,772** | **8,838** | **9,783.05** | 590 | 9 |
| CASE3 | 36 | 5.45% | 4,410 | 12,866 | 4,819.67 | 915 | 4 |

## 評価

### CASE2 vs CASE0

- **ROI**: CASE2 が n_w=24, 30, 36 のすべてで CASE0 を上回る（30.10% vs 18.24%、15.34% vs 6.04%、11.12% vs 0.53%）。
- **max_drawdown**: CASE2 が全 horizon で CASE0 より小さい（6,698 vs 7,766 / 10,702 / 15,886）。
- **total_profit**: n_w=24 では CASE0（11,744）> CASE2（11,036）。n_w=30 では CASE2（6,908）> CASE0（4,796）。n_w=36 では CASE2（5,772）> CASE0（484）。
- **profit_per_1000_bets**: CASE2 が全 horizon で最大。
- **longest_losing_streak**: CASE0 は 4 で最短。CASE2 は 7（24,30）／9（36）で長い。

### CASE2 vs CASE3

- n_w=24: CASE3 が total_profit 最大（13,386）。CASE2 は ROI・max_dd・profit/1k で優位。
- n_w=30: CASE3 が total_profit 最大（7,282）。CASE2 は ROI・max_dd・profit/1k で優位。
- n_w=36: CASE2 が ROI・total_profit・max_dd・profit/1k で優位。

### 結論（採用判断ルールに基づく）

- **複数 horizon で total_profit が CASE0 より優位**: n_w=30 と n_w=36 の 2 horizon で CASE2 > CASE0。n_w=24 では CASE0 の方が profit は高い。
- **ROI・max_dd・profit/1k**: CASE2 が 3 horizon すべてで CASE0 を上回る。
- **採用判断**: total_profit のみで見ると「36 のみ CASE2 が CASE0 を上回る」わけではなく、30 と 36 の 2 horizon で優位。ただし n_w=24 では profit は CASE0/CASE3 に劣る。ROI 単独では判断しない方針に従い、**複合指標では CASE2 は効率・リスクで全 horizon 優位だが、絶対利益では n_w=24 で CASE0/CASE3 に及ばない**。
- **判定**: **条件付き採用**。strict evaluation の主軸としては、n_w=36 を標準とする場合は CASE2 採用でよい。n_w=24 を主に使う場合は CASE0 または CASE3 の方が total_profit は高いため、horizon に応じた使い分けを推奨。

## 考察

- CASE2 は **n_windows に強く依存しているわけではない**（24/30/36 いずれでも ROI・max_dd・profit/1k で CASE0 を上回る）。
- n_w=24 では期間が短く、CASE0 の bet 数多め（704）が利益を伸ばしている。CASE2 は bet を絞るため profit は 11,036 で CASE0 の 11,744 よりわずかに低い。
- 長期（n_w=36）では CASE2 が profit でも明確に優位。実運用で「長期評価を標準」とするなら CASE2 を主軸とする根拠は十分。
- 結果 JSON は `outputs/case2_robustness/exp0071_case2_robustness.json`。outputs は gitignore のため未コミット。
