# EXP-0061: Stop / Resume Rule Experiment

## 目的

CASE6 / CASE2 / MIX（CASE6+CASE2 50%）に、window 内で N 連敗したら残り bet を停止するルールを適用し、**max_drawdown・longest_losing_streak・total_profit** のバランスが改善するかを検証する。停止は当該 window のみ。次 window で自動再開。

## 比較対象（9 variants）

| # | variant | 戦略 | 停止ルール |
|---|---------|------|------------|
| 1 | CASE6_base | CASE6_top1_prob_le_035 | なし |
| 2 | CASE6_stop3 | 同上 | 3連敗で当該 window 内残り bet 停止 |
| 3 | CASE6_stop4 | 同上 | 4連敗で当該 window 内残り bet 停止 |
| 4 | CASE2_base | CASE2_base（EV≥4.60） | なし |
| 5 | CASE2_stop3 | 同上 | 3連敗で停止 |
| 6 | CASE2_stop4 | 同上 | 4連敗で停止 |
| 7 | MIX_base | CASE6 + CASE2 50% 混成 | なし |
| 8 | MIX_stop3 | 同上 | 3連敗で停止 |
| 9 | MIX_stop4 | 同上 | 4連敗で停止 |

## 固定条件

- selection: CASE6_top1_prob_le_035 / CASE2_base（EV≥4.60）/ 混成 50%
- switch: switch_dd4000
- prediction: outputs/ev_cap_experiments/rolling_roi_predictions
- windows: rolling windows
- n_windows: 24 / 30 / 36
- block_size: 6

---

## 1. 全体結果（n_windows=36）

| variant | ROI | total_profit | max_drawdown | profit/1k | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w | median_w | std_w | early_half | late_half | profit/dd |
|---------|-----|--------------|--------------|-----------|-----------|-------------|--------|--------|--------------|---------|----------|-------|------------|------------|-----------|
| CASE6_base | 18.47% | 8764 | 12618 | 16442.78 | 533 | 47460 | 14 | 22 | 5 | -2400 | -156 | 3080 | 2244 | 6520 | 0.69 |
| CASE6_stop3 | 41.97% | 4424 | 2980 | 37176.47 | 119 | 10540 | 5 | 31 | 12 | -300 | -240 | 1700 | -2216 | 6640 | 1.48 |
| CASE6_stop4 | 9.23% | 1264 | 4540 | 8154.84 | 155 | 13700 | 5 | 31 | 12 | -400 | -320 | 1697 | -3256 | 4520 | 0.28 |
| CASE2_base | 58.72% | 17592 | 6422 | 51288.63 | 343 | 29960 | 12 | 24 | 9 | -1100 | -390 | 2684 | 5766 | 11826 | 2.74 |
| CASE2_stop3 | 115.39% | 13708 | 1924 | 101540.74 | 135 | 11880 | 9 | 27 | 6 | -300 | -240 | 2425 | 6976 | 6732 | 7.12 |
| CASE2_stop4 | 122.23% | 19166 | 2806 | 107674.16 | 178 | 15680 | 11 | 25 | 6 | -400 | -320 | 2638 | 6016 | 13150 | 6.83 |
| MIX_base | 28.12% | 17560 | 15750 | 24978.66 | 703 | 62440 | 12 | 24 | 6 | -2655 | -332 | 4298 | 5127 | 12433 | 1.11 |
| MIX_stop3 | 64.68% | 7128 | 4306 | 57483.87 | 124 | 11020 | 5 | 31 | 18 | -450 | -240 | 2481 | -2356 | 9484 | 1.66 |
| MIX_stop4 | 27.11% | 3952 | 5832 | 23807.23 | 166 | 14580 | 5 | 31 | 18 | -600 | -320 | 2478 | -3436 | 7388 | 0.68 |

## 2. 頑健性比較（total_profit 順位）

| n_windows | 1位 | 2位 | 3位 | 4位 | 5位 | 6位 | 7位 | 8位 | 9位 |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 24 | MIX_base | CASE2_base | CASE2_stop4 | CASE6_base | CASE2_stop3 | MIX_stop3 | MIX_stop4 | CASE6_stop3 | CASE6_stop4 |
| 30 | MIX_base | CASE2_stop4 | CASE2_base | CASE2_stop3 | CASE6_base | MIX_stop3 | CASE6_stop3 | MIX_stop4 | CASE6_stop4 |
| 36 | CASE2_stop4 | CASE2_base | MIX_base | CASE2_stop3 | CASE6_base | MIX_stop3 | CASE6_stop3 | MIX_stop4 | CASE6_stop4 |

- n_w=36 では CASE2_stop4 が total_profit 1 位。
- CASE6 / MIX の stop 系は常に下位。CASE2 の stop3/stop4 は 24/30/36 で上位を維持。

## 3. Block 比較（n_w=36, block_size=6）

代表のみ記載。block_index 0〜4（w0-w5 〜 w24-w29）。

### CASE2_base（攻め版 base）

| block | window_range | block_profit | block_roi | block_drawdown | block_bets | block_hits |
|-------|--------------|--------------|-----------|----------------|------------|------------|
| 0 | w0-w5 | 7678 | 128.39% | 2332 | 65 | 5 |
| 1 | w6-w11 | -1912 | -59.75% | 2008 | 40 | 2 |
| 2 | w12-w17 | 15252 | 269.47% | 900 | 62 | 8 |
| 3 | w18-w23 | -794 | -14.70% | 1614 | 56 | 5 |
| 4 | w24-w29 | -2808 | -53.59% | 2808 | 64 | 5 |

### CASE2_stop4（stop 採用候補）

| block | window_range | block_profit | block_roi | block_drawdown | block_bets | block_hits |
|-------|--------------|--------------|-----------|----------------|------------|------------|
| 0 | w0-w5 | 6960 | 254.01% | 1840 | 29 | 2 |
| 1 | w6-w11 | -944 | -51.30% | 1280 | 23 | 1 |
| 2 | w12-w17 | 12510 | 443.62% | 1120 | 30 | 4 |
| 3 | w18-w23 | 304 | 9.87% | 910 | 32 | 3 |
| 4 | w24-w29 | -668 | -33.74% | 728 | 24 | 3 |

- CASE2_stop4 は block 単位の drawdown が base より小さく、後半 block の損失も抑制されている。

## 4. 停止ルール評価

- **longest_losing_streak**: CASE2 のみ stop で短縮（base 9 → stop3/stop4 で 6）。CASE6 は base 5 → stop で 12 に悪化。MIX は base 6 → stop で 18 に悪化。
- **max_drawdown**: 全戦略で stop により改善。CASE2 は 6422 → 1924（stop3）/ 2806（stop4）。CASE6/MIX も数値上は改善するが、bet 激減に伴う副次的効果。
- **total_profit**: CASE2_stop4 は base より増加（19166 vs 17592）。CASE2_stop3 は減少（13708）。CASE6/MIX は stop でいずれも大幅減少。
- **どれに stop が効くか**: **CASE2 にのみ**、longest_lose 短縮・max_dd 改善・profit 維持または増加が同時に達成。CASE6/MIX は profit 毀損と longest_lose 悪化のため不採用。

## 5. 解釈

- 攻め戦略（CASE2）はもともと連敗が長くなりやすく、window 内で「N 連敗で止める」ことで、その window の追加損失を切り、次 window で再開する設計が有効。
- 標準戦略（CASE6）は bet 数が多く分散しているため、stop を入れると早期に止まりがちで、利益機会を削りつつ、window 単位の連敗窓数（longest_losing_streak）はむしろ増えている（止まった窓が「小損失の負け窓」として並ぶため）。
- 混成（MIX）は CASE6 と CASE2 のベットが混在するため、stop で同様に利益激減・longest_lose 悪化。

## 6. 採用判断

**結論: 3. CASE2 のみ stop 採用**

- CASE2_stop4: total_profit 増（19166）、max_drawdown 改善（2806）、longest_losing_streak 6（base と同程度）、profit/dd 6.83 で実運用で扱いやすい。
- CASE2_stop3: max_dd・longest_lose は改善するが total_profit は base より減少。より保守的にしたい場合のオプション。
- CASE6 / MIX には stop ルールを採用しない（現状維持）。

---

- 実行コマンド: `python3 -m kyotei_predictor.tools.run_exp0061_stop_resume_rules --n-windows-list 24,30,36`
- 結果 JSON: `outputs/selection_verified/exp0061_stop_resume_rules_results.json`
