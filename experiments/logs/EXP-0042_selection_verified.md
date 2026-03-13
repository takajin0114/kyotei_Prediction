# Experiment: EXP-0042 selection 条件厳密再検証

## experiment id

EXP-0042

## purpose

EXP-0041 により、bet 単位で stake / payout を厳密に整合させると全 sizing variant が赤字であることが判明した。次に、これまで有望と判断していた selection 条件を、EXP-0041 と同じ厳密な bet 単位評価で再検証し、どの条件が厳密評価で最もマシか（損失が小さいか）を確認して今後の探索方針を正しい土台に戻す。

## DB 存在確認結果と使用パス

- **確認したパス**: `kyotei_predictor/data/kyotei_races.sqlite`（リポジトリルート基準）。
- **実在確認**: ローカルで実在を確認。実行時に `_resolve_db_path()` で上記デフォルトを解決し、`db_path_resolved.exists()` で存在確認を行った。存在しない場合はエラーで終了する。
- **使用パス**: 未指定時は `_REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"`。本実行ではデフォルトを使用し、絶対パスで DB を参照した。

## selection variant 定義

stake は全 variant で同額固定（1 bet = 100 円）。比較する selection のみ変更。

| variant     | 条件 |
|-------------|------|
| baseline_a  | skip_top20pct + 3≤EV<5 |
| baseline_b  | skip_top20pct + 3≤EV<5 + prob≥0.05（EXP-0038 採用条件の厳密再検証） |
| baseline_c  | skip_top20pct + 4≤EV<5 |
| baseline_d  | skip_top20pct + 3≤EV<6 |
| baseline_e  | skip_top20pct + 3≤EV<5 + prob≥0.08 |
| baseline_f  | skip_top20pct + 3≤EV<8 |

## 厳密評価ロジック

EXP-0041 と同一。

- **stake**: 全 bet 100（固定）。
- **hit のとき**: payout = stake × odds。
- **外れのとき**: payout = 0。
- **profit**: profit = payout - stake。
- odds / hit は repo から race_data・odds_data を取得し、bet 単位で算出。

## EXP-0041 との関係

- 評価ロジックに差分はない（stake 固定 100、payout = stake×odds if hit、profit = payout - stake）。EXP-0041 は sizing を比較し、EXP-0042 は selection を比較する。
- EXP-0041 の baseline_fixed は「3≤EV<5 + prob≥0.05」固定だったため、EXP-0042 の baseline_b と同一条件。bet 集合の取り方（日付・skip_top20pct の対象レース集合）が同一であれば、baseline_b の結果は EXP-0041 の baseline_fixed と一致する想定（実装上、EXP-0042 では「odds が取れる selected_bet を全件列挙してから variant ごとにフィルタ」しているため、レースプールは一致）。

## 実装内容

- ツール: `kyotei_predictor/tools/run_exp0042_selection_verified.py`
- 処理: (1) DB パス存在確認（未指定時は repo root 基準のデフォルト）→ (2) 既存 rolling predictions 読み込み → (3) 日付ごとにレースを max_ev 降順で並べ skip_top20pct 適用 → (4) variant ごとの selection 条件で bet を抽出 → (5) 各 bet で odds / hit / payout / profit を厳密計算 → (6) window ごと・全体で集計 → (7) 各 variant の成績比較を出力。

## 実行コマンド

```bash
cd /path/to/kyotei_Prediction
# DB 未指定時は kyotei_predictor/data/kyotei_races.sqlite を参照（repo root 基準）
python3 -m kyotei_predictor.tools.run_exp0042_selection_verified --n-windows 18
# または明示
python3 -m kyotei_predictor.tools.run_exp0042_selection_verified --db-path kyotei_predictor/data/kyotei_races.sqlite --n-windows 18
```

## 結果表（n_windows=18, stake=100 固定）

| variant    | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | race_count | hit_count | hit_rate | total_stake | avg_odds | avg_ev  | avg_prob |
|------------|---------|--------------|--------------|----------------------|-----------|-------------|-----------|----------|-------------|----------|---------|----------|
| baseline_a | -8.54%  | -32,350      | 65,050       | -8,537.87            | 3,789     | 3,562       | 182       | 4.8%     | 378,900    | 80.51    | 3.89    | 0.231    |
| baseline_b | -5.42%  | -13,360      | 28,980       | -5,419.88            | 2,465     | 2,406       | 175       | 7.1%     | 246,500    | 22.70    | 3.93    | 0.341    |
| baseline_c | **-5.17%** | **-8,410** | 46,130       | **-5,165.85**        | 1,628     | 1,604       | 81        | 4.98%    | 162,800    | 84.42    | 4.48    | 0.285    |
| baseline_d | -18.41% | -93,130      | 113,140      | -18,412.42           | 5,058     | 4,694       | 257       | 5.08%    | 505,800    | 81.63    | 4.30    | 0.267    |
| baseline_e | -11.63% | -24,640      | 34,470       | -11,633.62           | 2,118     | 2,083       | 167       | 7.88%    | 211,800    | 16.55    | 3.94    | 0.387    |
| baseline_f | -10.71% | -74,380      | 130,390      | -10,714.49           | 6,942     | 6,369       | 347       | 5.0%     | 694,200    | 85.05    | 5.01    | 0.310    |

## 解釈

1. **過去に有望と見えた条件の厳密評価**
   - **baseline_b**（EXP-0038 採用: 3≤EV<5 + prob≥0.05）は厳密評価でも相対的にマシで、ROI -5.42%、total_profit -13,360、max_drawdown 28,980。EXP-0041 の baseline_fixed（同一 selection）と同水準。
   - **baseline_c**（4≤EV<5）が**最も損失が小さい**: ROI -5.17%、total_profit -8,410、profit_per_1000_bets -5,165.85。bet_count が少ない（1,628）分、絶対損失も小さい。
   - **baseline_a**（3≤EV<5、prob 制約なし）は -8.54%、-32,350 と悪化。prob フィルタの有効性が厳密評価でも支持される。
   - **baseline_d**（3≤EV<6）、**baseline_f**（3≤EV<8）は EV 上限を緩めると bet 数・total_stake が増え、損失・max_drawdown が大きくなる。
   - **baseline_e**（prob≥0.08）は prob を厳しくすると -11.63%、-24,640 と baseline_b より悪化。

2. **信頼できる条件の整理**
   - 厳密評価で**最もマシなのは baseline_c（4≤EV<5）**。次点が baseline_b（3≤EV<5 + prob≥0.05）。いずれも赤字だが、再現性のある「損失を抑える」条件として 4≤EV<5 または 3≤EV<5+prob≥0.05 を採用可能。
   - 全条件が赤字のため「黒字条件を無理に作る」のではなく、「厳密評価で最も信頼できる条件」を基準に今後の selection 探索を行う。

## 採用判断

- **厳密評価の正**: EXP-0042 を selection 比較の正とする。EXP-0041 で評価系を厳密化し、EXP-0042 で selection 条件を厳密再採点した。
- **採用候補**: **baseline_c（skip_top20pct + 4≤EV<5）** が ROI・total_profit・profit_per_1000_bets で最良。**baseline_b（skip_top20pct + 3≤EV<5 + prob≥0.05）** が次点で、従来の EXP-0038 採用条件と一致する。
- **max_drawdown**: baseline_b が 28,980 で baseline_c の 46,130 より小さい。リスクをより抑えるなら baseline_b を選ぶ選択肢もある。
- 今後の探索方針: 厳密評価を前提に、4≤EV<5 または 3≤EV<5+prob≥0.05 を土台に、他軸（会場・閾値微調整等）を必要時に検証する。

## 結果 JSON

outputs/selection_verified/exp0042_selection_verified_results.json
