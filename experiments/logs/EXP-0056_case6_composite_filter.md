# EXP-0056: CASE6 ベース複合条件（CASE6 + 軽EVフィルタ）

## 目的

EXP-0055 で CASE6 を実運用版として採用。本実験では CASE6（top1_prob≤0.35）をベースに EV 底上げ（4.30 / 4.40 / 4.50）を追加し、実運用標準として CASE6 単体でよいか、CASE6+軽EVフィルタへ置き換えるべきかを判断する。

## 条件

- **比較**: baseline, CASE6_top1_prob_le_035, CASE6+EV≥4.30, CASE6+EV≥4.40, CASE6+EV≥4.50
- **固定**: d_hi475 ベース・同一予測・窓・switch_dd4000、block_size=6
- **n_windows_list**: 24, 30, 36

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0056_case6_composite_filter --n-windows-list 24,30,36
```

## 主要結果表（n_w=36）

| variant                | ROI   | total_profit | max_dd  | profit/1k | bet_count | lose_w | longest_lose |
|------------------------|-------|--------------|---------|-----------|-----------|--------|---------------|
| baseline               | 0.53% | 484          | 15,886  | 469       | 1,031     | 22     | 4             |
| CASE6_top1_prob_le_035 | 18.47%| 8,764        | 12,618  | 16,443    | 533       | 22     | 5             |
| CASE6_ev_ge_430        | 18.47%| 8,764        | 12,618  | 16,443    | 533       | 22     | 5             |
| CASE6_ev_ge_440        | 22.09%| 8,050        | 11,660  | 19,586    | 411       | 25     | 10            |
| CASE6_ev_ge_450        | 44.14%| 11,608       | 6,840   | 39,084    | 297       | 27     | 10            |

（CASE6 と CASE6_ev_ge_430 は同一条件のため結果一致。）

## 頑健性（rank by total_profit）

| n_w | 1位 | 2位 | 3位 | 4位 | 5位 |
|-----|-----|-----|-----|-----|-----|
| 24  | CASE6 / CASE6_ev_ge_430 | CASE6_ev_ge_450 | CASE6_ev_ge_440 | baseline | — |
| 30  | CASE6_ev_ge_450 | CASE6 / CASE6_ev_ge_430 | CASE6_ev_ge_440 | baseline | — |
| 36  | CASE6_ev_ge_450 | CASE6 / CASE6_ev_ge_430 | CASE6_ev_ge_440 | baseline | — |

## ブロック別 profit（n_w=36）

- **CASE6**: [4340, -2096, 16650, -2010, -5608, -2512]。block 2 依存が大きい。
- **CASE6_ev_ge_440**: [4100, -2688, 14890, -1720, -4980, -1552]。同様に block 2 寄り。
- **CASE6_ev_ge_450**: [5780, -2880, 13010, -1210, -2580, -512]。block 2 は依然大きいが、後半ブロックの赤字は縮小。

## 解釈

1. **CASE6 単体 vs 複合**
   - CASE6+EV≥4.50 は profit・ROI・max_dd で最良だが、bet_count 297・longest_lose 10 となり尖りが強い。実運用の「標準」には向かない。
   - CASE6+EV≥4.40 は CASE6 単体より profit 低下（8,050 vs 8,764）、longest_lose 10 で悪化。複合のメリットなし。
   - CASE6 単体（= CASE6_ev_ge_430）が、bet 533・longest_lose 5・profit 8,764 で最もバランスが良い。

2. **EV を上げた場合**
   - EV≥4.50 で利益は伸びるが bet が 297 まで減少し、longest_losing_streak も 10 に伸びる。実運用標準としての bet_count は不足気味。

3. **ブロック依存**
   - 全条件で block 2（w12–w17）の利益が大きい。CASE6_ev_ge_450 は後半ブロックの赤字が小さく、ブロック間の偏りはやや緩和されるが、bet 減・連敗伸長のトレードオフが大きい。

4. **実運用標準としてのバランス**
   - 総合すると **CASE6 単体**が、利益・bet_count・longest_lose・ブロック偏りのバランスで最も実運用向き。

## 採用判断

- **結論**: **CASE6 単体を標準採用する。CASE6+軽EVフィルタへの置き換えは行わない。**
- **理由**:
  - CASE6+EV≥4.50 は数値上有利だが bet 297・longest_lose 10 のため、実運用の「標準」よりは攻め用オプションとして扱うのが妥当。
  - CASE6+EV≥4.40 は CASE6 単体より劣る。
  - 実運用標準候補としては、EXP-0055 の結論どおり **CASE6_top1_prob_le_035 単体**を採用し、複合条件は追加しない。

## 結果 JSON

- `outputs/selection_verified/exp0056_case6_composite_filter_results.json`
