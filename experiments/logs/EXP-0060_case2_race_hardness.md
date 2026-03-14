# EXP-0060: CASE2 Race Hardness Filter Experiment

## 目的

「CASE2 は難しいレース（top1_probability が低い）に強い」という仮説を検証する。CASE2_base（EV≥4.60）に top1_prob ≤ 0.35 / 0.40 / 0.45 の hardness フィルタを追加した 4 条件を比較し、**longest_losing_streak 短縮・profit 維持・profit/max_drawdown 改善** の同時達成を評価する。

## 条件

| variant        | 条件 |
|----------------|------|
| CASE2_base     | EV ≥ 4.60 |
| CASE2_hard_35  | EV ≥ 4.60, top1_probability ≤ 0.35 |
| CASE2_hard_40  | EV ≥ 4.60, top1_probability ≤ 0.40 |
| CASE2_hard_45  | EV ≥ 4.60, top1_probability ≤ 0.45 |

- **固定**: selection d_hi475 系・switch_dd4000・同一予測・rolling windows（n_w=24/30/36）

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0060_case2_race_hardness --n-windows-list 24,30,36
```

## 1 全体比較（n_w=36）

| variant        | ROI    | total_profit | max_dd  | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w | median_w | early_half | late_half | profit/dd |
|----------------|--------|--------------|---------|-------------|-----------|-------------|--------|--------|--------------|----------|----------|-------------|-----------|------------|
| CASE2_base     | 58.72% | 17,592       | 6,422   | 51,289      | 343       | 29,960      | 12     | 24     | **9**        | -1,360   | -390      | 21,018      | -3,426    | 2.7393     |
| CASE2_hard_35  | 123.38%| 18,828       | 6,340   | 108,832     | 173       | 15,260      | 7      | 28     | 16           | -800     | -320      | 21,610      | -2,782    | **2.9697** |
| CASE2_hard_40  | 111.46%| 17,968       | 6,860   | 98,186      | 183       | 16,120      | 7      | 28     | 16           | -880     | -320      | 21,270      | -3,302    | 2.6192     |
| CASE2_hard_45  | 107.21%| 18,568       | 6,696   | 94,254      | 197       | 17,320      | 9      | 27     | 12           | -960     | -400      | 21,706     | -3,138    | 2.7730     |

## 2 頑健性比較（rank by total_profit）

| n_w | 1位 | 2位 | 3位 | 4位 |
|-----|-----|-----|-----|-----|
| 24  | CASE2_hard_45 | CASE2_hard_35 | CASE2_hard_40 | CASE2_base |
| 30  | CASE2_hard_45 | CASE2_hard_35 | CASE2_base | CASE2_hard_40 |
| 36  | CASE2_hard_35 | CASE2_hard_45 | CASE2_hard_40 | CASE2_base |

hardness 付きが全 n_w で CASE2_base より profit 順位が上。順位は n_w により変動（24 で hard_45 1 位、36 で hard_35 1 位）。

## 3 block 比較（n_w=36, block_size=6）

- **CASE2_base**: block_profit 例 [7678, -1912, 15252, -794, -2808, 176]。block 2 依存・後半悪化。
- **CASE2_hard_35**: block あたり bet 減・block_profit 変動大。後半 block の赤字は base よりやや緩和（late_half_profit -2782 vs base -3426）。
- **CASE2_hard_45**: longest_lose 12 で hard_35/40（16）より短いが、CASE2_base（9）より長い。

## 4 CASE2 の安定性

- **bet_count**: base 343 → hard_35 173, hard_40 183, hard_45 197。hardness で約半減。
- **longest_losing_streak**: base 9 が最良。hard_35/40 は 16、hard_45 は 12 でいずれも悪化。
- **block 依存**: 全条件で block 2（w12–w17）の利益が大きい。hardness で bet が減り block 間のばらつきは維持または増大。
- **late_half_profit**: base -3426、hard_35 -2782、hard_40 -3302、hard_45 -3138。hard_35 がややマシ。

## 採用判断ルールの照合

採用候補条件（CASE2_base より **すべて** 満たすこと）:
1. longest_losing_streak 短縮  
2. profit 維持  
3. profit/max_drawdown 改善  

| variant        | profit維持 | longest_lose短縮 | profit/dd改善 |
|----------------|------------|------------------|----------------|
| CASE2_hard_35  | ○          | ✗ (9→16)         | ○             |
| CASE2_hard_40  | ○          | ✗ (9→16)         | ✗             |
| CASE2_hard_45  | ○          | ✗ (9→12)         | △ (微増)      |

**いずれも longest_losing_streak が短縮していない**（CASE2_base の 9 が最良）ため、3 条件同時達成はなし。

## 結論の分類

**1. CASE2_base 維持**

- hardness フィルタ（top1_prob ≤ 0.35/0.40/0.45）は **profit 維持・profit/dd 改善** を実現するが、**longest_losing_streak は悪化**（9 → 12〜16）。採用判断ルールの「longest_lose 短縮」を満たす条件はなく、攻め戦略は **CASE2_base（EV≥4.60）のまま** とする。
- 利益・効率を優先し連敗伸長を許容する場合は、**CASE2_hard_35**（profit/dd 2.97・profit 18,828）を攻め用オプションとして扱うことは可能。

## 結果 JSON

- `outputs/selection_verified/exp0060_case2_race_hardness_results.json`
