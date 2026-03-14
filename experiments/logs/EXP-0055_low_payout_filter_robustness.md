# EXP-0055: Low Payout Filter Robustness Comparison

## 目的

EXP-0054 で低配当回避フィルタが有効と確認された。本実験では baseline / CASE2 / CASE4 / CASE5 / CASE6 を **n_windows=24, 30, 36** で比較し、長期で強い候補と実運用向き安定候補を切り分ける。

## 条件

- **比較対象**: baseline, CASE2_ev_ge_460, CASE4_odds_ge_12, CASE5_odds_ge_15, CASE6_top1_prob_le_035
- **固定**: d_hi475 + switch_dd4000、block_size=6
- **n_windows_list**: 24, 30, 36

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0055_low_payout_filter_robustness --n-windows-list 24,30,36
```

## 1 全体結果表（n_w=36）

| variant                | ROI   | total_profit | max_dd   | profit/1k | bet_count | losing_w | longest_lose |
|------------------------|-------|--------------|----------|-----------|-----------|----------|--------------|
| baseline               | 0.53% | 484          | 15,886   | 469       | 1,031     | 22       | 4            |
| CASE2_ev_ge_460        | 58.72%| 17,592       | 6,422    | 51,289    | 343       | 24       | 9            |
| CASE4_odds_ge_12       | 11.75%| 6,012        | 14,358   | 10,456    | 575       | 21       | 5            |
| CASE5_odds_ge_15       | 19.15%| 8,520        | 12,810   | 17,040    | 500       | 23       | 10           |
| CASE6_top1_prob_le_035 | 18.47%| 8,764        | 12,618   | 16,443    | 533       | 22       | 5            |

## 2 頑健性比較（24 / 30 / 36）

**rank by total_profit**

| n_w | 1位 | 2位 | 3位 | 4位 | 5位 |
|-----|-----|-----|-----|-----|-----|
| 24  | CASE2 | CASE5 | CASE6 | CASE4 | baseline |
| 30  | CASE2 | CASE6 | CASE5 | CASE4 | baseline |
| 36  | CASE2 | CASE6 | CASE5 | CASE4 | baseline |

- CASE2 は 24/30/36 いずれでも profit 1 位。
- CASE6 は 30・36 で 2 位。24 では CASE5 が 2 位。
- 順位は期間延長でおおむね安定（CASE2 > CASE6/CASE5 > CASE4 > baseline）。

**n_w=24 サマリ**: baseline profit 11,744 / CASE2 20,224 / CASE4 15,252 / CASE5 17,172 / CASE6 16,884。  
**n_w=30 サマリ**: CASE2 が最良、CASE6 が 2 位（profit 11,276）、CASE5 10,712、CASE4 9,244、baseline は後半で悪化。

## 3 ブロック比較（n_w=36, block_size=6）

- **CASE2**: block_profits = [7678, -1912, 15252, -794, -2808, 176]。block 2（w12–w17）で 15,252 と利益の大部分を稼ぎ、他ブロックは小幅または赤字。特定期間依存が強い。
- **CASE6**: ブロック間のばらつきは CASE2 より小さく、longest_lose=5 で安定。
- **CASE4**: bet 575、longest_lose 5、max_dd 14,358。バランス型。
- **baseline**: 全ブロック合計で僅黒字、後半ブロックで悪化。

## 4 CASE2 尖り度

- **bet_count**: 343（他 variant 500〜1,031 に対し最少）。
- **longest_losing_streak**: 9（CASE6 は 5、CASE4 は 5）。
- **ブロック依存**: 利益の多くを block 2 に依存。block_profit_share で見ても block 2 が支配的。主軸化すると期間依存リスクが高い。

## 5 解釈

- **高リターン候補**: CASE2（profit・ROI 最大、max_dd 最小）。ただし bet 少・longest_lose 長・ブロック依存大のため攻め用に留める。
- **安定候補**: CASE6（profit 2 位、longest_lose 5、bet 533）、CASE4（bet 575、longest_lose 5）。CASE6 は高リターンと安定の両方に分類。
- **不採用候補**: なし（全 variant が baseline を上回る）。

## 6 採用判断

- **結論**: **(3) CASE2 を攻め版、CASE6 を実運用版として 2 本立て採用**。
- **理由**:  
  - CASE2 は ROI・profit・max_dd で最良だが、bet 343・longest_lose 9・block 2 依存が強く、主軸化はリスクが高い。攻め用オプションとして扱う。  
  - CASE6 は 24/30/36 で一貫して 2 位前後、longest_lose 5・bet 533 で実運用向き。実運用の標準候補として格上げする。  
  - baseline は維持のまま、低配当フィルタとして CASE6 を標準・CASE2 をオプションで追加する形とする。

## 結果 JSON

- `outputs/selection_verified/exp0055_low_payout_filter_robustness_results.json`
