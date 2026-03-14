# Experiment: EXP-0044 EV帯超微調整（厳密評価）

## experiment id

EXP-0044

## purpose

EXP-0043 により厳密評価で黒字化した有望条件（4.3≤EV<4.9 帯）の周辺を、0.05〜0.10 刻みで超微調整し、ROI・total_profit・max_drawdown のさらなる改善を狙う。4.3≤EV<4.9 より良い帯があるか、上限/下限を少し動かすだけで ROI が伸びるか、prob≥0.05 を付けるべきか外すべきかを確認する。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック（EXP-0043 と同一）

- stake = 100（全 bet 固定）
- hit のとき payout = stake × odds、外れのとき payout = 0
- profit = payout - stake
- odds / hit は repo から race_data・odds_data を取得し bet 単位で算出

## variant 一覧と条件定義

| variant     | ev_lo | ev_hi | prob_min | 条件 |
|-------------|-------|-------|----------|------|
| reference_1 | 4.3   | 4.9   | —        | EXP-0043 variant_j 再掲 |
| reference_2 | 4.3   | 4.9   | 0.05     | EXP-0043 variant_l 再掲 |
| variant_a   | 4.25  | 4.85  | —        | 4.25≤EV<4.85 |
| variant_b   | 4.25  | 4.85  | 0.05     | 4.25≤EV<4.85, prob≥0.05 |
| variant_c   | 4.30  | 4.80  | —        | 4.30≤EV<4.80 |
| variant_d   | 4.30  | 4.80  | 0.05     | 4.30≤EV<4.80, prob≥0.05 |
| variant_e   | 4.35  | 4.90  | —        | 4.35≤EV<4.90 |
| variant_f   | 4.35  | 4.90  | 0.05     | 4.35≤EV<4.90, prob≥0.05 |
| variant_g   | 4.40  | 4.85  | —        | 4.40≤EV<4.85 |
| variant_h   | 4.40  | 4.85  | 0.05     | 4.40≤EV<4.85, prob≥0.05 |
| variant_i   | 4.20  | 4.90  | —        | 4.20≤EV<4.90 |
| variant_j   | 4.20  | 4.90  | 0.05     | 4.20≤EV<4.90, prob≥0.05 |
| variant_k   | 4.30  | 4.95  | —        | 4.30≤EV<4.95 |
| variant_l   | 4.30  | 4.95  | 0.05     | 4.30≤EV<4.95, prob≥0.05 |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0044_ev_band_fine_tuning_verified.py`
- EXP-0042 / EXP-0043 の `_resolve_db_path`, `_max_ev_for_race`, `_all_bets_for_race`, `_filter_bets_by_selection` を流用。SELECTION_VARIANTS のみ 4.3≤EV<4.9 周辺の超微調整用に変更。
- 処理: DB 確認 → rolling predictions 読み込み → 日付ごと max_ev 降順 → skip_top20pct → variant ごとに EV/prob フィルタ → stake=100 で payout/profit を bet 単位計算 → 集計・出力。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0044_ev_band_fine_tuning_verified --n-windows 18
```

## 結果表（n_windows=18, stake=100）

| variant     | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | race_count | hit_rate | prof_w | lose_w | avg_profit/race |
|-------------|---------|--------------|--------------|-------------|-----------|------------|----------|--------|--------|-----------------|
| reference_1 | 12.34%  | 11,660       | 30,740       | 12,338.62   | 945       | 935        | 5.29%    | 5      | 13     | 12.47           |
| reference_2 | 5.82%   | 3,820        | 15,040       | 5,823.17    | 656       | 654        | 7.32%    | 6      | 12     | 5.84            |
| variant_a   | 16.50%  | 15,840       | 28,080       | 16,500.00   | 960       | 949        | 5.52%    | 6      | 12     | 16.69           |
| variant_b   | 12.59%  | 8,400        | 13,980       | 12,593.70   | 667       | 665        | 7.65%    | 8      | 10     | 12.63           |
| variant_c   | **27.57%** | **22,440** | 25,220       | **27,567.57** | 814     | 806        | 5.65%    | 6      | 12     | 27.84           |
| variant_d   | 18.34%  | 10,400       | **11,820**   | 18,342.15   | 567       | 565        | 7.76%    | 8      | 10     | 18.41           |
| variant_e   | 19.02%  | 16,360       | 29,120       | 19,023.26   | 860       | 851        | 5.23%    | 5      | 13     | 19.22           |
| variant_f   | 9.92%   | 5,920        | 15,020       | 9,916.25    | 597       | 595        | 7.20%    | 7      | 11     | 9.95            |
| variant_g   | **30.46%** | **21,660** | 24,950       | **30,464.14** | 711     | 703        | 5.49%    | 4      | 14     | 30.81           |
| variant_h   | 13.17%  | 6,520        | 13,250       | 13,171.72   | 495       | 493        | 7.47%    | 7      | 11     | 13.23           |
| variant_i   | 3.03%   | 3,370        | 32,490       | 3,030.58    | 1,112     | 1,100      | 5.04%    | 5      | 13     | 3.06            |
| variant_j   | 0.56%   | 430          | 16,690       | 555.56      | 774       | 772        | 6.98%    | 6      | 12     | 0.56            |
| variant_k   | 10.46%  | 10,670       | 31,360       | 10,460.78   | 1,020     | 1,009      | 5.49%    | 5      | 13     | 10.57           |
| variant_l   | 7.40%   | 5,230        | 13,960       | 7,397.45    | 707       | 705        | 7.64%    | 6      | 12     | 7.42            |

## 上位条件の解釈

### reference_1（4.3≤EV<4.9）より改善したか

- reference_1: ROI 12.34%、total_profit 11,660、max_dd 30,740。
- **variant_g**（4.40≤EV<4.85）: ROI **30.46%**（+18.12%pt）、profit 21,660、max_dd 24,950。ROI・profit ともに reference_1 を上回り、max_dd も約 5,800 改善。
- **variant_c**（4.30≤EV<4.80）: ROI **27.57%**（+15.23%pt）、profit 22,440（最高）、max_dd 25,220。利益最大・ROI も大きく改善。
- **variant_e**（4.35≤EV<4.90）: ROI 19.02%、profit 16,360。
- **variant_a**（4.25≤EV<4.85）: ROI 16.50%、profit 15,840。
- 結論: **4.3≤EV<4.9 を狭めたり下限を上げる（4.30〜4.40、上限 4.80〜4.85）と ROI・profit が明確に改善**している。

### reference_2（4.3≤EV<4.9 + prob≥0.05）より改善したか

- reference_2: ROI 5.82%、total_profit 3,820、max_dd 15,040。
- **variant_d**（4.30≤EV<4.80, prob≥0.05）: ROI **18.34%**（+12.52%pt）、profit 10,400、max_dd **11,820**（reference_2 より約 3,220 改善）。prob 付き条件では **ROI・profit・DD のバランスが最も良い**。
- **variant_b**（4.25≤EV<4.85, prob≥0.05）: ROI 12.59%、profit 8,400、max_dd 13,980。reference_2 を上回る。
- **variant_h**（4.40≤EV<4.85, prob≥0.05）: ROI 13.17%、max_dd 13,250。
- 結論: **prob≥0.05 を付ける場合は、帯を 4.30≤EV<4.80 に絞ると reference_2 より大幅改善**（特に variant_d）。

### ROI だけでなく DD や bet_count のバランス

- **variant_g**: ROI 最高（30.46%）だが、losing_windows=14 で安定性はやや劣る。bet_count 711 で reference_1（945）より少ないが、profit は約 2 倍。
- **variant_d**: prob≥0.05 付きで max_dd が最小クラス（11,820）。profitable_windows=8、losing_windows=10 で reference_2 よりバランスが良い。実務で「リスクを抑えたい」場合は variant_d が有力。
- **variant_c**: total_profit 最大（22,440）、ROI 27.57%。bet_count 814 で十分な件数。ROI と利益の両立。
- **variant_i**（4.20≤EV<4.90）: 帯を広げると ROI が 3.03% に落ち、max_dd 32,490 と悪化。4.2 まで広げるのは不利。
- **variant_j**（4.20≤EV<4.90, prob≥0.05）: ROI 0.56% とほぼトントン。採用メリットは小さい。

## 採用判断

- **総合**: 超微調整により **reference_1 / reference_2 をいずれも上回る条件が複数得られた**。改善幅は実務的に意味がある（ROI +15%pt 以上、max_dd 数千円単位の改善）。
- **ROI・利益重視**: **variant_g**（4.40≤EV<4.85、prob なし）を採用。ROI 30.46%、profit 21,660。実運用候補の第一候補とする。
- **利益絶対量重視**: **variant_c**（4.30≤EV<4.80、prob なし）。total_profit 22,440 が最大。ROI 27.57% も高水準。
- **リスク・安定性重視**: **variant_d**（4.30≤EV<4.80、prob≥0.05）。max_dd 11,820 で最小クラス。ROI 18.34%、profit 10,400。prob 付きで運用する場合は variant_d を推奨。
- **judgment**: **adopt**。実運用候補を **skip_top20pct + 4.40≤EV<4.85**（variant_g）に更新。リスクを抑えたい場合は **skip_top20pct + 4.30≤EV<4.80 + prob≥0.05**（variant_d）。結果 JSON: outputs/selection_verified/exp0044_ev_band_fine_tuning_verified_results.json。
