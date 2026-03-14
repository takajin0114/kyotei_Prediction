# EXP-0057: CASE6 標準 + 攻め用小ロット混成運用

## 目的

CASE6 を標準戦略（ロット1.0）とし、攻め用（CASE2_ev_ge_460 または CASE6_ev_ge_450）を 0.25 / 0.50 倍ロットで併用した場合の total_profit・max_drawdown・longest_losing_streak を比較し、**実運用標準を CASE6 単体のままとするか、混成へ昇格させるか**を判断する。

## 条件

- **比較**: baseline, CASE6 単体, CASE2 単体, CASE6_ev_ge_450 単体, CASE6+CASE2 25%, CASE6+CASE2 50%, CASE6+CASE6_ev_ge_450 25%, CASE6+CASE6_ev_ge_450 50%
- **固定**: 同一予測・窓・switch_dd4000（baseline ref_profit から算出）、block_size=6
- **混成ルール**: 同一レースで買い目重複時は (odds, hit) をキーに **stake を加算**（CASE6 分 + 攻め用 0.25 または 0.50 倍）
- **n_windows_list**: 24, 30, 36
- **DB**: パス存在確認を明示（`_resolve_db_path`）

## 実行コマンド

```bash
python3 -m kyotei_predictor.tools.run_exp0057_mixed_standard_attack --n-windows-list 24,30,36
```

## 主要結果表（n_w=36）

| variant                  | ROI    | total_profit | max_dd   | profit/1k   | bet_count | total_stake | lose_w | longest_lose | early_half | late_half |
|--------------------------|--------|--------------|----------|-------------|-----------|-------------|--------|--------------|------------|-----------|
| baseline                 | 0.53%  | 484          | 15,886   | 469         | 1,031     | 91,100      | 22     | 4            | 14,928     | -14,444   |
| CASE6_single             | 18.47% | 8,764        | 12,618   | 16,443      | 533       | 47,460      | 22     | 5            | 18,894     | -10,130   |
| CASE2_single             | 58.72% | 17,592       | 6,422    | 51,289      | 343       | 29,960      | 24     | 9            | 21,018     | -3,426    |
| CASE6_ev_ge_450_single   | 44.14% | 11,608       | 6,840    | 39,084      | 297       | 26,300      | 27     | 10           | 15,910     | -4,302    |
| CASE6_C2_25              | 23.95% | 13,162       | 14,184   | 18,776      | 701       | 54,950      | 23     | 6            | 24,149     | -10,987   |
| CASE6_C2_50              | 28.12% | 17,560       | 15,750   | 25,050      | 701       | 62,440      | 24     | 6            | 29,403     | -11,843   |
| CASE6_450_25             | 21.59% | 11,666       | 14,328   | 21,929     | 532       | 54,035      | 23     | 6            | 22,872     | -11,206   |
| CASE6_450_50             | 24.04% | 14,568       | 16,038   | 27,383     | 532       | 60,610      | 23     | 6            | 26,849     | -12,281   |

## 窓別・前半後半（n_w=36）

| variant        | profitable_windows | losing_windows | worst_window_profit | median_window_profit | window_profit_std | early_half_profit | late_half_profit |
|----------------|--------------------|----------------|---------------------|----------------------|-------------------|-------------------|------------------|
| baseline       | 14                 | 22             | -2,960              | -636                 | 2,654             | 14,928            | -14,444          |
| CASE6_single   | 14                 | 22             | -2,400              | -720                 | 2,639             | 18,894            | -10,130          |
| CASE2_single   | 12                 | 24             | -1,360              | -390                 | 2,283             | 21,018            | -3,426           |
| CASE6_ev_ge_450_single | 9 | 27             | -1,200              | -440                 | 2,166             | 15,910            | -4,302           |
| CASE6_C2_25    | 13                 | 23             | -2,528              | -758                 | 3,146             | 24,149            | -10,987          |
| CASE6_C2_50    | 12                 | 24             | -2,680              | -756                 | 3,672             | 29,403            | -11,843          |
| CASE6_450_25   | 13                 | 23             | -2,625              | -830                 | 3,131             | 22,872            | -11,206          |
| CASE6_450_50   | 13                 | 23             | -2,850              | -940                 | 3,638             | 26,849            | -12,281          |

## 頑健性（rank by total_profit）

| n_w | 1位 | 2位 | 3位 | 4位 | 5位 | 6位 | 7位 | 8位 |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 24  | CASE6_C2_50 | CASE6_450_50 | CASE6_C2_25 | CASE6_450_25 | CASE2_single | CASE6_single | CASE6_ev_ge_450_single | baseline |
| 30  | CASE6_C2_50 | CASE2_single | CASE6_450_50 | CASE6_C2_25 | CASE6_450_25 | CASE6_ev_ge_450_single | CASE6_single | baseline |
| 36  | CASE2_single | CASE6_C2_50 | CASE6_450_50 | CASE6_C2_25 | CASE6_450_25 | CASE6_ev_ge_450_single | CASE6_single | baseline |

## ブロック別（n_w=36）概要

- **baseline**: block_profit [2038, -1104, 13994, -3184, -6948, -4312]。block 2 依存・後半悪化。
- **CASE6_single**: [4340, -2096, 16650, -2010, -5608, -2512]。同様に block 2 寄り、後半赤字。
- **CASE2_single**: 全ブロックで profit 変動大。後半ブロックの赤字は相対的に小さい。
- **混成**: CASE6 単体より bet_count 増・total_profit は CASE6_C2_50 が CASE6 単体を上回る（17,560 vs 8,764）。max_dd は混成で増加（14k〜16k）。

## 解釈

1. **CASE6 単体 vs 混成の total_profit**
   - n_w=36 で CASE6_C2_50 は 17,560、CASE6 単体 8,764 の約 2 倍。CASE6_C2_25 も 13,162 で CASE6 単体を上回る。
   - CASE6_450_25/50 は CASE6 単体より profit 増（11,666 / 14,568 vs 8,764）だが、CASE2 混成ほどは伸びない。

2. **攻め用追加による max_drawdown・longest_losing_streak**
   - CASE6 単体: max_dd 12,618、longest_lose 5。
   - CASE6_C2_25: max_dd 14,184（+約12%）、longest_lose 6。
   - CASE6_C2_50: max_dd 15,750（+約25%）、longest_lose 6。
   - CASE6_450_25/50: max_dd 14k〜16k、longest_lose 6。CASE6 単体より悪化するが、CASE2 単体の 9 や CASE6_ev_ge_450 単体の 10 よりは穏やか。

3. **許容できる混成比率**
   - 25% 混成（CASE6_C2_25 / CASE6_450_25）は max_dd・longest_lose の悪化が限定的。50% 混成は profit は伸びるが max_dd が 15k 台となり、許容は資金量次第。

4. **CASE2 併用 vs CASE6_ev_ge_450 併用**
   - **CASE2 併用**: total_profit が大きい（CASE6_C2_50 で 17,560）。bet_count 701 で CASE6 単体より多い。扱いやすさは「攻め用」として明確。
   - **CASE6_ev_ge_450 併用**: 同じ CASE6 系のため条件が近く、重複ベットが多く stake 加算になりやすい。profit は CASE2 混成より劣るが、条件の一貫性は高い。

5. **標準運用の判断**
   - **CASE6 単体維持**: リスク（max_dd・longest_lose）を抑えたい場合は現状のままが無難。
   - **混成へ昇格**: 利益を優先し、max_dd 1.5 万前後の増加を許容するなら、**CASE6 + CASE2 25%** または **CASE6 + CASE2 50%** を「標準＋攻めオプション」として運用可能。CASE6_ev_ge_450 混成は「CASE6 のみで統一したい」場合の候補。

## 採用判断

- **結論**: **実運用標準は当面 CASE6 単体のままとする。** 混成（CASE6 + CASE2 25% または 50%）は **攻め用オプション** として許容し、資金とリスク許容度に応じて併用するか選択する。
- **理由**:
  - 混成は total_profit を大きく改善するが、max_drawdown・longest_losing_streak が悪化する。
  - 標準を「安定軸」に据え、攻め用を「オプション」とする 2 本立てが、EXP-0055 方針と整合する。
  - CASE2 併用の方が profit 伸びが大きく扱いやすい。CASE6_ev_ge_450 併用は CASE6 系統一時に検討可。

## 結果 JSON

- `outputs/selection_verified/exp0057_mixed_standard_attack_results.json`

## 変更ファイル一覧

- 新規: `kyotei_predictor/tools/run_exp0057_mixed_standard_attack.py`
- 新規: `experiments/logs/EXP-0057_mixed_strategy.md`
- 更新: `experiments/leaderboard.md`, `docs/ai_dev/chat_context.md`, `docs/ai_dev/project_status.md`
