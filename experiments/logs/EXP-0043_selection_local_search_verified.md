# Experiment: EXP-0043 selection 条件局所探索（厳密評価）

## experiment id

EXP-0043

## purpose

EXP-0042 で厳密評価で最もマシだった selection は baseline_c（4≤EV<5）と baseline_b（3≤EV<5+prob≥0.05）だったが、いずれも赤字だった。今回、baseline_c / baseline_b の周辺で EV 帯と prob 閾値を微調整し、厳密評価のまま赤字幅を縮小できるか、0%付近まで近づけられるか、実運用候補をより絞り込めるかを検証する。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック（EXP-0042 と同一）

- stake = 100（全 bet 固定）
- hit のとき payout = stake × odds、外れのとき payout = 0
- profit = payout - stake
- odds / hit は repo から race_data・odds_data を取得し bet 単位で算出

## variant 一覧と条件定義

| variant     | ev_lo | ev_hi | prob_min | 条件 |
|-------------|-------|-------|----------|------|
| reference_1 | 3.0   | 5.0   | 0.05     | baseline_b 相当 |
| reference_2 | 4.0   | 5.0   | —        | baseline_c 相当 |
| variant_a   | 4.0   | 5.0   | —        | 4≤EV<5 |
| variant_b   | 4.0   | 5.0   | 0.03     | 4≤EV<5, prob≥0.03 |
| variant_c   | 4.0   | 5.0   | 0.05     | 4≤EV<5, prob≥0.05 |
| variant_d   | 4.0   | 4.8   | —        | 4≤EV<4.8 |
| variant_e   | 4.0   | 4.8   | 0.03     | 4≤EV<4.8, prob≥0.03 |
| variant_f   | 4.0   | 4.8   | 0.05     | 4≤EV<4.8, prob≥0.05 |
| variant_g   | 4.2   | 5.0   | —        | 4.2≤EV<5 |
| variant_h   | 4.2   | 5.0   | 0.03     | 4.2≤EV<5, prob≥0.03 |
| variant_i   | 4.2   | 5.0   | 0.05     | 4.2≤EV<5, prob≥0.05 |
| variant_j   | 4.3   | 4.9   | —        | 4.3≤EV<4.9 |
| variant_k   | 4.3   | 4.9   | 0.03     | 4.3≤EV<4.9, prob≥0.03 |
| variant_l   | 4.3   | 4.9   | 0.05     | 4.3≤EV<4.9, prob≥0.05 |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0043_selection_local_search_verified.py`
- EXP-0042 の `_resolve_db_path`, `_max_ev_for_race`, `_all_bets_for_race`, `_filter_bets_by_selection` を流用。variant リストのみ局所探索用に変更。
- 処理: DB 確認 → rolling predictions 読み込み → 日付ごと max_ev 降順 → skip_top20pct → variant ごとに EV/prob フィルタ → stake=100 で payout/profit を bet 単位計算 → 集計・出力。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0043_selection_local_search_verified --n-windows 18
```

## 結果表（n_windows=18, stake=100）

| variant     | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | race_count | hit_rate | prof_w | lose_w | avg_profit/race |
|-------------|---------|--------------|--------------|-------------|-----------|------------|----------|--------|--------|-----------------|
| reference_1 | -5.42%  | -13,360      | 28,980       | -5,419.88   | 2,465     | 2,406      | 7.1%     | 7      | 11     | -5.55           |
| reference_2 | -5.17%  | -8,410       | 46,130       | -5,165.85   | 1,628     | 1,604      | 4.98%    | 5      | 13     | -5.24           |
| variant_a   | -5.17%  | -8,410       | 46,130       | -5,165.85   | 1,628     | 1,604      | 4.98%    | 5      | 13     | -5.24           |
| variant_b   | -7.44%  | -9,450       | 32,820       | -7,435.09   | 1,271     | 1,261      | 6.22%    | 7      | 11     | -7.49           |
| variant_c   | -6.36%  | -7,200       | 22,680       | -6,360.42   | 1,132     | 1,125      | 6.89%    | 7      | 11     | -6.40           |
| variant_d   | **+4.07%**  | **+5,460**   | 38,040       | **+4,068.55**  | 1,342     | 1,321      | 4.92%    | 6      | 12     | 4.13            |
| variant_e   | -1.98%  | -2,080       | 24,390       | -1,980.95   | 1,050     | 1,041      | 6.10%    | 7      | 11     | -2.00           |
| variant_f   | -1.86%  | -1,730       | 19,410       | -1,860.22   | 930       | 923        | 6.77%    | 6      | 12     | -1.87           |
| variant_g   | **+0.22%**  | **+280**     | 34,830       | +220.99     | 1,267     | 1,254      | 5.29%    | 6      | 12     | 0.22            |
| variant_h   | -8.57%  | -8,460       | 23,410       | -8,571.43   | 987       | 984        | 6.59%    | 7      | 11     | -8.60           |
| variant_i   | **+1.74%**  | **+1,540**   | **16,130**   | +1,736.19   | 887       | 885        | 7.33%    | 7      | 11     | 1.74            |
| variant_j   | **+12.34%** | **+11,660**  | 30,740       | +12,338.62  | 945       | 935        | 5.29%    | 5      | 13     | 12.47           |
| variant_k   | -5.42%  | -3,980       | 19,540       | -5,422.34   | 734       | 731        | 6.54%    | 5      | 13     | -5.44           |
| variant_l   | **+5.82%**  | **+3,820**   | **15,040**   | +5,823.17   | 656       | 654        | 7.32%    | 6      | 12     | 5.84            |

## 上位条件の解釈

1. **baseline_c より改善したか**  
   reference_2（baseline_c）は ROI -5.17%、total_profit -8,410。**variant_d, variant_g, variant_i, variant_j, variant_l** がこれを上回り、いずれも黒字または 0% 付近。とくに **variant_j**（4.3≤EV<4.9, prob なし）が ROI +12.34%、**variant_l**（4.3≤EV<4.9, prob≥0.05）が +5.82%、**variant_d**（4≤EV<4.8）が +4.07%、**variant_i**（4.2≤EV<5, prob≥0.05）が +1.74%、**variant_g**（4.2≤EV<5）が +0.22%。

2. **baseline_b より改善したか**  
   reference_1（baseline_b）は ROI -5.42%。上記 5 条件はいずれも baseline_b より大きく改善している。

3. **ROI と DD・bet_count のバランス**  
   - **variant_j**: ROI 最高（+12.34%）だが、max_drawdown 30,740、bet_count 945。losing_windows が 13 と多く、window 間のばらつきはある。
   - **variant_l**: ROI +5.82%、max_drawdown **15,040**（黒字条件で最小）、bet_count 656。DD が小さくバランスが良い。
   - **variant_i**: ROI +1.74%、max_drawdown 16,130、bet_count 887。ROI は控えめだが DD が小さく、bet 数も確保されている。
   - **variant_d**: ROI +4.07%、bet_count 1,342 で最多。total_profit +5,460。ボリュームと利益のバランスが良い。
   - **variant_g**: ROI +0.22%、ほぼトントン。bet_count 1,267。

## 採用判断

- **厳密評価のまま、局所探索で複数条件が黒字または 0% 付近まで改善した**。採用候補は次のとおり。
- **推奨（バランス重視）**: **variant_l**（4.3≤EV<4.9, prob≥0.05）。ROI +5.82%、max_drawdown 15,040 で黒字条件中最小、bet_count 656。DD と利益のバランスが良い。
- **ROI 最優先**: **variant_j**（4.3≤EV<4.9, prob なし）。ROI +12.34%、total_profit +11,660。bet_count 945、max_dd 30,740。リスク許容するなら採用可。
- **ボリューム重視**: **variant_d**（4≤EV<4.8）。ROI +4.07%、bet_count 1,342、total_profit +5,460。
- **控えめリスク**: **variant_i**（4.2≤EV<5, prob≥0.05）。ROI +1.74%、max_dd 16,130、bet_count 887。
- 実運用では、**variant_l** を主候補とし、DD をさらに抑えたい場合は **variant_i**、ROI を優先する場合は **variant_j** を選択肢とする。

## 結果 JSON

outputs/selection_verified/exp0043_selection_local_search_verified_results.json
