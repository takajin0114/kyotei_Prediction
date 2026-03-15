# EXP-0079: schedule / ref_profit 再最適化（new_main 向け）

## 1 目的

- 主軸戦略は new_main（4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09）に更新されたが、ref_profit と switch_dd4000 の基準は旧主軸ベースのままの可能性がある。
- new_main に合わせた ref_profit / schedule へ再最適化したときに profit / drawdown / 安定性が改善するかを確認する。
- **主軸そのものの有効性確認ではなく**、risk control の基準を主軸に合わせて最適化すべきかを判断する。

## 2 実験設計

### 対象ベット（共通）

- **new_main**: 4.50 ≤ EV < 4.90, 0.05 ≤ prob < 0.09
- calibration = sigmoid, skip_top20pct = true

### 比較 CASE

| CASE | ref_profit 定義 | dd_threshold | 説明 |
|------|-----------------|--------------|------|
| CASE0_old_ref | 4.30 ≤ EV < 4.75, prob ≥ 0.05（旧基準） | 4000 | 現行のまま |
| CASE1_new_ref | 4.50 ≤ EV < 4.90, prob ≥ 0.05（新基準） | 4000 | ref のみ new_main に合わせる |
| CASE2_new_ref_dd3000 | 新基準 | 3000 | 閾値厳しめ |
| CASE3_new_ref_dd5000 | 新基準 | 5000 | 閾値緩め |

### horizon

- n_windows = 24, 30, 36, 48

### 評価指標

- ROI, total_profit, max_drawdown, profit_per_1000_bets, bet_count
- longest_losing_streak, block_profit
- schedule_switch_count（stake=80 の window 数）

## 3 実験結果

### 結果表（variant × horizon）

| variant | n_w | ROI(%) | total_profit | max_drawdown | profit/1k | bet_count | longest_lose | switch_cnt |
|---------|-----|--------|--------------|--------------|-----------|-----------|--------------|------------|
| CASE0_old_ref | 24 | 211.79 | 15,630 | 2,780 | 192,963 | 81 | 6 | 11 |
| CASE1_new_ref | 24 | 199.20 | 13,466 | 2,860 | 166,247 | 81 | 6 | 19 |
| CASE2_new_ref_dd3000 | 24 | 203.69 | 13,566 | 2,760 | 167,481 | 81 | 6 | 21 |
| CASE3_new_ref_dd5000 | 24 | 199.20 | 13,466 | 2,860 | 166,247 | 81 | 6 | 19 |
| CASE0_old_ref | 30 | 143.75 | 13,570 | 4,200 | 128,019 | 106 | 12 | 16 |
| CASE1_new_ref | 30 | 130.89 | 11,466 | 3,760 | 108,170 | 106 | 12 | 25 |
| CASE2_new_ref_dd3000 | 30 | 133.56 | 11,566 | 3,760 | 109,113 | 106 | 12 | 27 |
| CASE3_new_ref_dd5000 | 30 | 130.89 | 11,466 | 3,760 | 108,170 | 106 | 12 | 25 |
| CASE0_old_ref | 36 | 159.36 | 17,338 | 5,400 | 139,823 | 124 | 12 | 22 |
| CASE1_new_ref | 36 | 149.35 | 15,234 | 4,960 | 122,855 | 124 | 12 | 31 |
| CASE2_new_ref_dd3000 | 36 | 151.82 | 15,334 | 4,960 | 123,661 | 124 | 12 | 33 |
| CASE3_new_ref_dd5000 | 36 | 149.35 | 15,234 | 4,960 | 122,855 | 124 | 12 | 31 |
| CASE0_old_ref | 48 | 155.14 | 19,858 | 5,400 | 134,176 | 148 | 12 | 34 |
| CASE1_new_ref | 48 | 148.67 | 18,524 | 4,960 | 125,162 | 148 | 12 | 36 |
| CASE2_new_ref_dd3000 | 48 | 150.68 | 18,624 | 4,960 | 125,838 | 148 | 12 | 38 |
| CASE3_new_ref_dd5000 | 48 | 147.87 | 18,484 | 4,960 | 124,892 | 148 | 12 | 34 |

### block_profit（6 block 分割、代表 n_w=36）

- **CASE0_old_ref**: [7450, -1440, 11760, -2140, -2060, 3768]（勝3 / 負3）
- **CASE1_new_ref**: [7370, -1440, 9296, -1760, -2000, 3768]（勝3 / 負3）
- CASE2 / CASE3 も new_ref と同様に block 構成は同じで、絶対値のみ CASE1 前後の水準。

### 観察

1. **total_profit**: 全 horizon で CASE0_old_ref が最大。new_ref にすると約 1,300〜2,200 程度減少。
2. **max_drawdown**: n_w=30/36/48 では new_ref（CASE1〜3）が 3,760 / 4,960 で、CASE0 の 4,200 / 5,400 より改善。
3. **ROI / profit_per_1000_bets**: CASE0 が全 horizon で最良。bet_count は全 CASE 同一（ベット対象が new_main 固定のため）。
4. **schedule_switch_count**: new_ref の方が発動回数が多い（保守モードに入る窓が増える）→ 利益機会を抑えている。
5. **CASE2 (dd3000)**: CASE1 よりわずかに profit が高いが差は小さく、switch はさらに多い。
6. **CASE3 (dd5000)**: CASE1 と同程度。n_w=48 では CASE1 よりやや低い。

## 4 採用判断

- **total_profit**: 旧 ref（CASE0）が全 horizon で優位。new_ref への変更は利益を減らす。
- **max_drawdown**: new_ref の方が 30/36/48 で改善するが、profit 減少とトレードオフ。
- **36/48 での一貫性**: 両 horizon とも CASE0 が profit・ROI・profit/1k で最良。new_ref は DD のみ改善。
- **旧 ref_profit を捨てる根拠**: なし。利益が減るため、現状の「ref_profit は旧基準（4.30–4.75）、ベットは new_main」の組み合わせを維持するのが総合的に有利。

**結論**

- **ref_profit / schedule の new_main 基準への再最適化は adopt しない（hold）。**
- 主軸ベットは new_main（4.50–4.90, 0.05–0.09）のまま、risk control の ref_profit は**旧基準（4.30 ≤ EV < 4.75, prob ≥ 0.05）＋ switch_dd4000 を維持**する。
- 「新主軸に合わせて risk 基準も揃える」ことで DD は改善するが、profit が一貫して減少するため、実運用の完成度向上としては現時点では採用しない。

## 5 各 CASE メモ

| CASE | 採用可否 | メモ |
|------|----------|------|
| CASE0_old_ref | **採用（現行維持）** | 全指標で profit 最大。ref は旧基準のまま継続。 |
| CASE1_new_ref | reject | profit 減。DD 改善のみでは置き換え理由にならない。 |
| CASE2_new_ref_dd3000 | reject | CASE1 よりやや profit 高いが、差は小さく switch 増。 |
| CASE3_new_ref_dd5000 | reject | CASE1 と同程度〜やや低い。 |

## 6 出力

- 結果 JSON: `outputs/schedule_refprofit_reopt/exp0079_schedule_refprofit_reopt.json`（gitignore のため未コミット）
- ツール: `python3 -m kyotei_predictor.tools.run_exp0079_schedule_refprofit_reopt`
