# Experiment: EXP-0050 switch_dd4000 長期頑健性確認

## experiment id

EXP-0050

## purpose

EXP-0049 で推奨となった switch_dd4000 が、24 windows の局所最適ではなく、より長い期間（n_windows=30, 36）でも優位性が再現するか確認する。d_hi475 を前提に normal_only / conservative_only / switch_dd4000 / switch_dd5000 を 24・30・36 で比較し、順位安定性と profit/DD バランスを評価する。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック

- 選抜: d_hi475 固定（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）。
- 通常 stake=100、保守 stake=80。累積DD（normal_only の window 利益を基準）が閾値以上になった window は stake=80。
- n_windows = 24 / 30 / 36 の3水準で同一指標を算出。予測未生成分は rolling validation（n_windows=36）で補完済み。

## 比較対象

| variant            | 説明 |
|--------------------|------|
| normal_only        | 常に stake=100 |
| conservative_only  | 常に stake=80 |
| switch_dd4000      | 累積DD≥4000 で当該 window を 80（EXP-0049 推奨） |
| switch_dd5000      | 累積DD≥5000 で当該 window を 80（比較用再掲） |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0050_switch_dd4000_robustness_verified.py`
- 最大 n_windows（36）まで rolling を回し、24・30・36 それぞれで先頭 n 窓のみを使い集計。EXP-0049 と同様の日別 stake スケジュール・ref_profit ベース累積DD。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0050_switch_dd4000_robustness_verified --n-windows-list 24,30,36
```

## 結果表（必須指標）

### n_windows=24

| variant            | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w  | early_half | late_half | median_w | std_w   |
|--------------------|---------|--------------|-------------|-------------|-----------|-------------|--------|--------|--------------|----------|------------|-----------|----------|---------|
| normal_only        | 13.65%  | 9,610        | 9,420       | 13,650.57   | 704       | 70,400      | 10     | 14     | 4            | -2,810   | -270       | 9,880     | -425     | 3146.98 |
| conservative_only  | 13.65%  | 7,688        | 7,536       | 10,920.45   | 704       | 56,320      | 10     | 14     | 4            | -2,248   | -216       | 7,904     | -340     | 2517.58 |
| switch_dd4000      | **18.24%** | **11,744** | **7,766**   | **16,681.82** | 704   | 64,400      | 10     | 14     | 4            | -2,800   | 934        | 10,810    | -386     | 3059.93 |
| switch_dd5000      | 16.33%  | 10,814       | 7,766       | 15,360.80   | 704       | 66,220      | 10     | 14     | 4            | -2,800   | 934        | 9,880     | -386     | 3086.29 |

### n_windows=30（主評価）

| variant            | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w  | early_half | late_half | median_w | std_w   |
|--------------------|---------|--------------|-------------|-------------|-----------|-------------|--------|--------|--------------|----------|------------|-----------|----------|---------|
| normal_only        | 1.02%   | 900         | 12,690      | 1,016.95    | 885       | 88,500      | 12     | 18     | 4            | -3,700   | 2,980      | -2,080    | -670     | 2968.30 |
| conservative_only  | 1.02%   | 720         | 10,152      | 813.56      | 885       | 70,800      | 12     | 18     | 4            | -2,960   | 2,384     | -1,664    | -536     | 2374.64 |
| switch_dd4000      | **6.04%** | **4,796**  | **10,702**  | **5,419.21** | 885   | 79,420      | 12     | 18     | 4            | -2,960   | 4,590     | 206       | -582     | 2850.54 |
| switch_dd5000      | 4.76%   | 3,866       | 10,878      | 4,368.36    | 885       | 81,240      | 12     | 18     | 4            | -2,960   | 4,184     | -318      | -654     | 2869.35 |

### n_windows=36（補助評価）

| variant            | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w  | early_half | late_half | median_w | std_w   |
|--------------------|---------|--------------|-------------|-------------|-----------|-------------|--------|--------|--------------|----------|------------|-----------|----------|---------|
| normal_only        | -4.35%  | -4,490       | 19,170      | -4,355.00   | 1,031     | 103,100     | 14     | 22     | 4            | -3,700   | 12,970    | -17,460   | -795     | 2782.26 |
| conservative_only  | -4.35%  | -3,592       | 15,336      | -3,484.00   | 1,031     | 82,480      | 14     | 22     | 4            | -2,960   | 10,376    | -13,968   | -636     | 2225.81 |
| switch_dd4000      | **0.53%** | **484**    | **15,886**  | **469.45**  | 1,031     | 91,100      | 14     | 22     | 4            | -2,960   | 14,928    | -14,444   | -636     | 2654.44 |
| switch_dd5000      | -0.48%  | -446        | 16,062      | -432.59     | 1,031     | 92,920      | 14     | 22     | 4            | -2,960   | 14,174    | -14,620   | -708     | 2669.75 |

## 解釈

- **24→30→36 の順位安定性**: いずれの n_windows でも **switch_dd4000 が total_profit ・ROI とも1位**。24 のみの局所最適ではない。
- **profit/DD バランス**:
  - n_w=24: switch_dd4000 が profit 最大（11,744）かつ max_dd は 7,766 で switch_dd5000 と同水準。
  - n_w=30: normal は profit 900・max_dd 12,690。switch_dd4000 は profit 4,796・max_dd 10,702 で、**profit 増・DD 減**の両立。
  - n_w=36: normal は赤字（-4,490）・max_dd 19,170。switch_dd4000 は**唯一黒字（484）**・max_dd 15,886 で、**黒字維持と DD 抑制**を両立。
- **longest_losing_streak**: 全条件で 4。悪化なし。
- **後半の悪化**: n_w=30/36 では late_half_profit が normal で大きくマイナス（-2,080 / -17,460）。switch_dd4000 は 30 で 206、36 で -14,444 と、36 では後半もマイナスだが normal よりマシで、全体では黒字に転じている。

## 採用判断

- **結論**: 30/36 でも switch_dd4000 の優位が維持されているため、**switch_dd4000 を「推奨オプション」から「実運用標準候補」へ格上げ**する。
- **採用判断ルールとの対応**:
  - ROI 単独では採用しない → 満たす（total_profit と max_drawdown のバランスを最重視）。
  - 30/36 で優位が維持されるなら実運用標準候補へ格上げ → **維持されているため格上げ**。
- **実運用**:
  - **実運用標準候補**: **switch_dd4000**（累積DD≥4000 で当該 window を stake=80）。通常版（d_hi475 stake=100）と並ぶ選択肢として標準候補とする。
  - 通常版主軸は維持。参考運用として conservative_only や switch_dd5000 も利用可能。
- **judgment**: **adopt**（実運用標準候補へ格上げ）。結果 JSON: outputs/selection_verified/exp0050_switch_dd4000_robustness_verified_results.json。
