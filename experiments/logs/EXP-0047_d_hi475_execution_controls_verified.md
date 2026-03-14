# Experiment: EXP-0047 d_hi475 運用制御の追加効果検証

## experiment id

EXP-0047

## purpose

EXP-0046 で主軸化した d_hi475（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）に対し、レースごとの点数制限と軽い防御ルールの効果を検証する。ROI を大きく毀損せず、max_drawdown・longest_losing_streak・worst_window_profit の改善を目指す。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック

- stake: base/cap1/cap2/top1_*/dd_guard_light は 100、sizing_80 は 80。
- payout = stake × odds if hit、外れは 0。
- profit = payout - stake。
- n_windows = 24。

## 比較対象（運用制御）

| variant        | 説明                         | レースあたり | dd_guard | stake |
|----------------|------------------------------|--------------|----------|-------|
| base           | 現行 d_hi475（制御なし）     | 全点         | なし     | 100   |
| cap1           | 最大1点（EV 上位）           | 1            | なし     | 100   |
| cap2           | 最大2点（EV 上位）           | 2            | なし     | 100   |
| top1_prob      | prob 上位1点のみ             | 1            | なし     | 100   |
| top1_ev        | EV 上位1点のみ               | 1            | なし     | 100   |
| dd_guard_light | 前 window が赤字なら次 window は賭けなし | 全点         | あり     | 100   |
| sizing_80      | base と同条件で stake=80     | 全点         | なし     | 80    |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0047_d_hi475_execution_controls_verified.py`
- 選抜は d_hi475 固定。skip_top20pct 適用後、各 variant でレースごとに cap/order を適用し、dd_guard_light は base の window_profits を参照して前 window 赤字時は当該 window の賭けをスキップ。
- 必須指標に加え average_bets_per_race, race_count を出力。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0047_d_hi475_execution_controls_verified --n-windows 24
```

## 結果表（n_windows=24）

| variant        | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | race_count | avg_b/r | prof_w | lose_w | longest_lose | worst_w  |
|----------------|---------|--------------|--------------|-------------|-----------|------------|---------|--------|--------|--------------|----------|
| base           | 13.65%  | 9,610        | 9,420        | 13,650.57   | 704       | 703        | 1.0     | 10     | 14     | 4            | -2,810   |
| cap1           | 13.81%  | 9,710        | 9,420        | 13,812.23   | 703       | 703        | 1.0     | 10     | 14     | 4            | -2,810   |
| cap2           | 13.65%  | 9,610        | 9,420        | 13,650.57   | 704       | 703        | 1.0     | 10     | 14     | 4            | -2,810   |
| top1_prob      | 13.81%  | 9,710        | 9,420        | 13,812.23   | 703       | 703        | 1.0     | 10     | 14     | 4            | -2,810   |
| top1_ev        | 13.81%  | 9,710        | 9,420        | 13,812.23   | 703       | 703        | 1.0     | 10     | 14     | 4            | -2,810   |
| dd_guard_light | 7.80%   | 2,270        | **5,900**    | 7,800.69    | 291       | 290        | 1.0     | 4      | 6      | **1**        | -2,800   |
| sizing_80      | 13.65%  | 7,688        | **7,536**   | 10,920.45   | 704       | 703        | 1.0     | 10     | 14     | 4            | **-2,248** |

## 解釈

- **base**: d_hi475 現行。avg_bets_per_race=1.0 のため、もともとほぼ 1 レース 1 点に近い。
- **cap1 / top1_ev / top1_prob**: 1 レース 1 点に揃えた結果、703 bets（1 レース分減少）で ROI がわずかに上昇（13.81%）、他指標は base と同等。実質 base と同等のため主軸の置き換えは不要。
- **cap2**: base と同一（既に多くが 1〜2 点のため cap2 で変化なし）。
- **dd_guard_light**: max_drawdown 5,900・longest_losing_streak 1 とリスクは大きく改善するが、bet 数 291 に減り total_profit 2,270 にとどまる。リスク回避用のオプションとして有効だが、主軸にはしない。
- **sizing_80**: ROI 13.65% を維持しつつ、max_drawdown 9,420→7,536、worst_window_profit -2,810→-2,248 と改善。longest_losing_streak は 4 のまま。利益は stake に比例して 7,688。**保守版**として「通常版 base / 保守版 sizing_80」の 2 本立てに適する。

## 採用判断

- **d_hi475 維持**しつつ、**通常版 / 保守版の 2 本立て採用**とする。
- **主軸（通常版）**: d_hi475 のまま（base）。stake=100、運用制御の追加は行わない（既にほぼ 1 レース 1 点のため cap1 等の効果は微小）。
- **保守版**: **sizing_80**（d_hi475 条件のまま stake=80）。ROI 維持で max_dd・worst_w を改善。リスクを抑えたい場合に使用。
- **オプション**: dd_guard_light は max_dd・longest_lose の抑制に有効だが bet 数が少なく利益が限られるため、極端なリスク回避時のみ参照。
- **judgment**: **adopt**（主軸 d_hi475 維持＋保守版 sizing_80 の 2 本立て）。結果 JSON: outputs/selection_verified/exp0047_d_hi475_execution_controls_verified_results.json。
