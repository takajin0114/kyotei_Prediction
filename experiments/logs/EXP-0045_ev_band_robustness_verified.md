# Experiment: EXP-0045 EV帯の頑健性確認（長期・複数分割）

## experiment id

EXP-0045

## purpose

EXP-0044 で採用した EV 帯（variant_g: 4.40≤EV<4.85、variant_d: 4.30≤EV<4.80 + prob≥0.05）が、n_w=18 の局所最適ではなく、より長い期間・複数分割でも再現するかを検証する。n_windows を 24 に拡張し、追加指標（longest_losing_streak / worst_window_profit / median_window_profit / window_profit_std）および前半・後半（early half / late half）の regime 差を確認する。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック（EXP-0044 と同一）

- stake = 100（全 bet 固定）
- hit のとき payout = stake × odds、外れのとき payout = 0
- profit = payout - stake
- odds / hit は repo から race_data・odds_data を取得し bet 単位で算出

## 比較対象 variant

| variant     | ev_lo | ev_hi | prob_min | 条件 |
|-------------|-------|-------|----------|------|
| reference_1 | 4.3   | 4.9   | —        | 4.3≤EV<4.9 |
| reference_2 | 4.3   | 4.9   | 0.05     | 4.3≤EV<4.9, prob≥0.05 |
| variant_g   | 4.40  | 4.85  | —        | EXP-0044 採用（メイン） |
| variant_d   | 4.30  | 4.80  | 0.05     | EXP-0044 採用（リスク重視） |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0045_ev_band_robustness_verified.py`
- EXP-0042 / EXP-0044 の verified ロジックを流用。variant は reference_1, reference_2, variant_g, variant_d の 4 つのみ。
- n_windows は 24 をデフォルト（30 はデータ範囲・実行時間の都合で任意実行）。
- 追加算出: profitable_windows, losing_windows, longest_losing_streak, worst_window_profit, median_window_profit, window_profit_std, early_half_profit, late_half_profit。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0045_ev_band_robustness_verified --n-windows 24
```

## 結果表（n_windows=24, stake=100）

| variant     | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | lose_w | longest_lose | worst_w  | median_w | early_half | late_half |
|-------------|---------|--------------|--------------|-------------|-----------|--------|--------------|----------|----------|------------|-----------|
| reference_1 | -3.54%  | -4,580       | 30,740       | -3,544.89   | 1,292     | 19     | 6            | -5,210   | -2,835   | 10,650     | -15,230   |
| reference_2 | -2.36%  | -2,120       | 15,040       | -2,355.56   | 900       | 18     | 6            | -3,600   | -1,045   | -6,990     | 4,870     |
| variant_g   | 9.52%   | 9,190        | 24,950       | 9,523.32    | 965       | 20     | **10**       | -4,210   | -1,930   | 17,410     | -8,220    |
| variant_d   | 7.02%   | 5,420        | **11,820**   | 7,020.73    | 772       | 14     | **4**        | **-3,100** | **-770** | -3,470   | 8,890     |

## 解釈

- **variant_g（4.40≤EV<4.85）**: n=24 でも黒字（ROI 9.52%、total_profit 9,190）だが、**longest_losing_streak=10** で 24 中 20 期間が赤字。後半（late_half）で -8,220 と悪化し、前半の +17,410 でかろうじて全体黒字。18 windows 時より不安定。
- **variant_d（4.30≤EV<4.80, prob≥0.05）**: ROI 7.02%（variant_g より低い）だが、**longest_losing_streak=4**、**losing_windows=14**、**max_drawdown=11,820** で最も安定。後半で +8,890 と良い。worst_window_profit -3,100、median -770 と他よりマシ。
- **reference_1 / reference_2**: 24 windows ではいずれも赤字。reference_2 は後半でプラスに転じているが、全体ではマイナス。
- **regime 差**: variant_g は前半有利・後半不利。variant_d は後半有利。長期で見ると variant_d の方が後半も含めてバランスが良い。

## 採用判断

- **総合**: 長期（n_w=24）では **variant_g は黒字を維持するが不安定性が高い**（longest_losing_streak=10、losing_windows=20）。**variant_d は ROI はやや劣るが安定性で上回る**（longest_losing_streak=4、max_dd 最小、後半も黒字）。
- **判断**: **variant_d を実運用主軸へ格上げ**する。variant_g は「高 ROI を狙うが連続負けリスクを許容する場合のサブ」とする。
- **実運用候補の更新**:
  - **主軸**: **skip_top20pct + 4.30≤EV<4.80 + prob≥0.05**（variant_d）。長期・前半後半のバランスと max_drawdown・longest_losing_streak を重視。
  - **サブ（リスク許容）**: skip_top20pct + 4.40≤EV<4.85（variant_g）。ROI を優先する場合のみ。
- **judgment**: **adopt**（採用判断の見直し）。結果 JSON: outputs/selection_verified/exp0045_ev_band_robustness_verified_results.json。
