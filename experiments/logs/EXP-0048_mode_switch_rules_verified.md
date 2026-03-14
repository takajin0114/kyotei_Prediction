# Experiment: EXP-0048 通常版/保守版モード切替ルール検証

## experiment id

EXP-0048

## purpose

EXP-0047 で採用した通常版（d_hi475 + stake=100）と保守版（d_hi475 + stake=80）について、window 単位の単純な切替ルールを検証する。total_profit を大きく落とさず、max_drawdown・longest_losing_streak・worst_window_profit を改善できる現実的なルールを探す。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: 起動時に `_resolve_db_path()` で解決し `exists()` を確認。ローカルで実在を確認済み。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用。

## 評価ロジック

- 選抜: d_hi475 固定（skip_top20pct + 4.30≤EV<4.75 + prob≥0.05）。
- 各 window で stake を 100 または 80 に設定。payout = stake × odds if hit、profit = payout - stake。
- 切替判定の参照: normal_only の window 別利益（ref_profit）。
- n_windows = 24。

## 比較対象（切替ルール）

| variant             | ルール概要 |
|---------------------|------------|
| normal_only         | 常に stake=100 |
| conservative_only   | 常に stake=80 |
| switch_after_2_loss | 直近2 window 連続赤字（ref）なら次 window は stake=80 |
| switch_after_3_loss | 直近3 window 連続赤字なら次 window は stake=80 |
| switch_dd5000       | 累積DD（ref 基準）が 5000 以上ならその window は stake=80 |
| recover_after_1win   | 2連続赤字で保守化、1 window 黒字で通常に復帰 |

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0048_mode_switch_rules_verified.py`
- 日別に「stake=100 時の利益・stake=80 時の利益」を事前計算し、ref = normal_only の window 別利益を算出。各 variant で stake_schedule[wi] を決定し、その schedule に従い集計。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
python3 -m kyotei_predictor.tools.run_exp0048_mode_switch_rules_verified --n-windows 24
```

## 結果表（n_windows=24）

| variant             | ROI     | total_profit | max_drawdown | profit/1k   | bet_count | total_stake | prof_w | lose_w | longest_lose | worst_w  |
|---------------------|---------|--------------|--------------|-------------|-----------|-------------|--------|--------|--------------|----------|
| normal_only         | 13.65%  | 9,610        | 9,420        | 13,650.57   | 704       | 70,400      | 10     | 14     | 4            | -2,810   |
| conservative_only   | 13.65%  | 7,688        | 7,536        | 10,920.45   | 704       | 56,320      | 10     | 14     | 4            | -2,248   |
| switch_after_2_loss | 15.24%  | 9,998        | 9,044        | 14,201.70   | 704       | 65,620      | 10     | 14     | 4            | -2,800   |
| switch_after_3_loss | 13.51%  | 9,224        | 9,882        | 13,102.27   | 704       | 68,260      | 10     | 14     | 4            | -2,810   |
| switch_dd5000       | **16.33%** | **10,814** | **7,766**    | **15,360.80** | 704   | 66,220      | 10     | 14     | 4            | -2,800   |
| recover_after_1win   | 13.37%  | 8,916        | 9,262        | 12,664.77   | 704       | 66,680      | 10     | 14     | 4            | -2,810   |

## 解釈

- **normal_only**: 基準。profit 9,610、max_dd 9,420。
- **conservative_only**: 利益 7,688、max_dd 7,536。DD は改善するが利益は比例して減少。
- **switch_after_2_loss**: profit 9,998（+388）、max_dd 9,044（-376）。ROI 15.24% と利益・DD ともわずかに改善。説明しやすいルール。
- **switch_after_3_loss**: max_dd 9,882 で normal より悪化。採用見送り。
- **switch_dd5000**: profit 10,814（+1,204）、max_dd 7,766（-1,654）。ROI 16.33%。利益を増やしつつ DD を明確に抑制。**最良バランス**。
- **recover_after_1win**: profit 8,916、max_dd 9,262。normal よりやや劣る。主軸候補外。

## 採用判断

- **結論**: **3) 通常版主軸 + 切替版をオプション化**とする。
- **主軸**: これまで通り **通常版固定**（d_hi475 + stake=100）。シンプルで説明しやすいため主軸は変更しない。
- **オプション（推奨）**: **switch_dd5000**（累積DD≥5000 で当該 window を stake=80 に保守化）。total_profit・ROI を伸ばしつつ max_drawdown を抑えられる。実運用で「DD が一定以上になったら一時的にスタケを下げる」として利用可能。
- **補助オプション**: **switch_after_2_loss**（直近2 window 連続赤字なら次 window を stake=80）。効果は小幅だがルールが分かりやすい。
- **judgment**: **adopt**（主軸は通常版維持、切替版をオプションとして採用）。結果 JSON: outputs/selection_verified/exp0048_mode_switch_rules_verified_results.json。
