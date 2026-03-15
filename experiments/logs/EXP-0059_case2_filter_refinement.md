# EXP-0059: CASE2 フィルタ改善（ノイズ削減）

## 目的

CASE2（攻め戦略）のノイズを削減し、**単独でも使える攻め戦略**に改善する。EV≥4.60 をベースに prob・predicted_odds・top1_prob を追加した 5 条件を比較する。

## 条件

| variant        | 条件 |
|----------------|------|
| CASE2_base     | EV ≥ 4.60（既存 CASE2） |
| CASE2_prob     | EV ≥ 4.60, prob ≥ 0.06 |
| CASE2_odds     | EV ≥ 4.60, predicted_odds ≥ 12 |
| CASE2_prob_odds| EV ≥ 4.60, prob ≥ 0.06, predicted_odds ≥ 12 |
| CASE2_full     | EV ≥ 4.60, prob ≥ 0.06, predicted_odds ≥ 12, top1_probability ≤ 0.35 |

- **固定**: 予測・窓・switch_dd4000 は EXP-0058 と同一

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0059_case2_filter_refinement --n-windows-list 24,30,36
```

## 主要結果表（n_w=36）

| variant         | ROI    | total_profit | max_dd  | profit/1k  | bet_count | longest_lose | total_stake | profit/dd |
|-----------------|--------|--------------|---------|------------|-----------|---------------|-------------|-----------|
| CASE2_base      | 58.72% | 17,592       | 6,422   | 51,289     | 343       | **9**         | 29,960      | **2.7393**|
| CASE2_prob      | 8.01%  | 2,242        | 5,742   | 6,984      | 321       | 7             | 27,980      | 0.3905    |
| CASE2_odds      | 107.85%| 17,688       | 6,960   | 95,097     | 186       | 16            | 16,400      | 2.5414    |
| CASE2_prob_odds | 16.21% | 2,338        | 6,100   | 14,256     | 164       | 16            | 14,420      | 0.3833    |
| CASE2_full      | 26.19% | 3,478        | 5,480   | 23,033     | 151       | 16            | 13,280      | 0.6347    |

## 評価（n_w=36、CASE2_base との比較）

| 観点 | CASE2_base | CASE2_prob | CASE2_odds | CASE2_prob_odds | CASE2_full |
|------|------------|------------|------------|-----------------|------------|
| 1. profit 維持 | — | ✗ (大幅減) | ○ (同程度) | ✗ | ✗ |
| 2. longest_lose 短縮 | — | ○ (9→7) | ✗ (9→16) | ✗ (16) | ✗ (16) |
| 3. profit/dd 改善 | — | ✗ | ✗ | ✗ | ✗ |

- **CASE2_prob**: 連敗は 9→7 に短縮するが、profit が 17,592→2,242 に大きく減少。単独攻め用としては不利。
- **CASE2_odds**: profit は維持（17,688）だが longest_lose が 16 に悪化。profit/dd も微減。
- **CASE2_prob_odds / CASE2_full**: profit・longest_lose・profit/dd いずれも CASE2_base に劣る。

## 解釈

- 追加フィルタ（prob≥0.06, odds≥12, top1≤0.35）は、**profit を維持したまま longest_losing_streak を短縮する**組み合わせは見つからなかった。
- CASE2_base（EV≥4.60）が、n_w=36 時点では **単独攻め戦略として最もバランスが良い**（profit 最大・profit/dd 最大・longest_lose 9）。
- 連敗短縮を最優先する場合は **CASE2_prob**（longest_lose 7）を選択可能だが、profit は約 1/8 に減少する。

## 採用判断

- **結論**: **攻め戦略は現行の CASE2（CASE2_base, EV≥4.60）を単独でもそのまま使用する。** フィルタ追加による「profit 維持かつ longest_lose 短縮」は達成されなかった。
- **単独攻め用**: CASE2_base をそのまま推奨。CASE2_prob はリスク抑制重視時のオプション（profit 大幅減を許容する場合）。

## 結果 JSON

- `outputs/selection_verified/exp0059_case2_filter_refinement_results.json`
