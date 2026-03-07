# EV ベッティング戦略モジュール

EV 戦略を本格的な betting system として拡張した内容の整理。
baseline B + calibration=sigmoid を基準とする。

---

## 0. 暫定主戦略と 1 本化フロー

- **暫定主戦略**: baseline B + **sigmoid** + **top_n=5** + **EV>=1.15** + **fixed**（1 点 100 円）。
- **1 本化フロー**: 学習 → 予測（selected_bets 付与）→ 検証 → サマリ保存 を一括実行。
  - **CLI**: `python -m kyotei_predictor.cli.run_strategy_b --train-start YYYY-MM-DD --train-end YYYY-MM-DD --predict-date YYYY-MM-DD --data-dir <raw>`  
  - **詳細**: **docs/STRATEGY_B_OPERATION.md**
- **再検証**: 複数 window で主戦略のみ実行 → **logs/strategy_b_validation_windows.json**。  
  `PYTHONPATH=. python3 kyotei_predictor/tools/strategy_b_validation_windows.py`
- **過去結果との差分**: なぜ以前はプラスで今回はマイナスになりうるかの条件整理 → **docs/STRATEGY_B_CONDITION_DIFF.md**

---

## 1. モジュール構成

| ファイル | 役割 |
|----------|------|
| `kyotei_predictor/betting/expected_value.py` | EV（期待リターン）計算。`expected_roi(probability, odds)`、`ev_above_threshold(...)` |
| `kyotei_predictor/betting/bet_sizing.py` | ベットサイズ。fixed / kelly_full / kelly_half。`kelly_fraction(p, odds)`、`compute_stake(...)` |
| `kyotei_predictor/betting/bankroll_simulation.py` | 資金シミュレーション。`simulate_bankroll(bets, ...)` → bankroll_curve, max_drawdown, sharpe_ratio, profit_factor。`build_bet_list_from_verify(predictions, details)` で検証結果から賭けリストを組み立て。 |

---

## 2. EV threshold sweep

### 目的

閾値 1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.20 で B top_n=5 を比較し、最適な EV 閾値を探索する。

### 記録指標

- ROI（%）
- hit_rate（%）
- bet_count
- profit
- mean_odds_placed（購入した点の平均オッズ）

### 実行方法

```bash
PYTHONPATH=. python3 kyotei_predictor/tools/ev_threshold_sweep.py
```

### 結果保存

- **logs/ev_threshold_sweep.json**

### EV threshold スイープ結果（実測）

条件: 1 window（train 2024-06-01〜06-15、test 06-16〜06-22）、calibration=sigmoid、B top_n=5。  
保存先: **logs/ev_threshold_sweep.json**

| ev_threshold | roi_pct | hit_rate_pct | bet_count | profit | mean_odds_placed |
|--------------|---------|--------------|-----------|--------|------------------|
| 1.02 | -14.02 | 4.21 | 722 | -10,120 | 219.46 |
| 1.05 | -19.08 | 3.74 | 716 | -13,660 | 221.04 |
| 1.08 | -18.05 | 3.74 | 707 | -12,760 | 223.47 |
| 1.10 | -17.58 | 3.74 | 703 | -12,360 | 224.59 |
| 1.12 | -16.99 | 3.74 | 698 | -11,860 | 225.91 |
| 1.15 | **-15.91** | 3.74 | **689** | **-10,960** | 228.40 |
| 1.20 | -23.47 | 3.27 | 675 | -15,840 | 232.31 |

- **採用理由**: この 1 window では全閾値でマイナス ROI。相対的に **EV>1.15** が最も損失が小さい（-15.91%、689 点）。1.12 も近いが 1.15 を採用。1.20 は ROI ・hit_rate とも悪化するため採用しない。bet_count は 675〜722 でいずれも極端に少なくない。
- **最適閾値**: **1.15**（本番デフォルト推奨）。代替として 1.10（やや多点・やや損失大）も選択可能。

---

## 3. Kelly betting 比較

### 方式

- **fixed**: 1 点あたり 100 円固定。
- **kelly_full**: 賭け率 f = (b×p - q) / b（b = odds - 1, p = 予測確率, q = 1-p）。stake = bankroll × f。
- **kelly_half**: stake = bankroll × 0.5 × f。

### 比較方法

rolling validation（4 window）で fixed と kelly_half の両方をシミュレーションし、同一の選定結果（selected_bets）に対して資金曲線・max_drawdown・Sharpe・profit_factor を比較する。

### 結果

- **logs/rolling_ev_strategy_compare.json** の `aggregate_by_strategy` に fixed / kelly_half の mean_max_drawdown, mean_sharpe_ratio を記録。

### fixed vs kelly_half 比較結果（実測）

条件: 4 window rolling（train 15日 / test 7日）、calibration=sigmoid。  
保存先: **logs/rolling_ev_strategy_compare.json** の `aggregate_by_strategy`。

| 戦略 | mean_roi_pct | positive_roi_windows | fixed mean_max_drawdown | fixed mean_sharpe | kelly_half mean_max_drawdown | kelly_half mean_sharpe |
|------|--------------|----------------------|--------------------------|-------------------|------------------------------|------------------------|
| B top_n=3 | -34.06 | 0/4 | 24,435 | -1.59 | 99,294 | -1.35 |
| B top_n=5 EV>1.10 | -23.88 | 1/4 | 30,863 | -1.53 | 99,755 | -1.58 |
| B top_n=5 EV>1.15 | **-21.94** | 1/4 | **29,738** | **-1.45** | 99,747 | -1.52 |

- **採用理由**: **fixed** を採用。理由は (1) 同一戦略で fixed の方が max_drawdown がはるかに小さい（約 2.5〜3 万 vs kelly_half 約 10 万）、(2) Sharpe はどちらも負で大きな差はないが fixed の方がややマシ（EV>1.15 で -1.45 vs -1.52）、(3) 資金変動が小さく運用しやすい。kelly_half はリスク・ドローダウンが大きいため本番主戦略にはしない。
- **bet sizing 推奨**: **fixed**（1 点 100 円）。リスク抑制版も fixed のまま、EV 閾値で厳しめ（1.15）にする。

---

## 4. Bankroll simulation

### 入力

- **predictions**: 予測リスト（selected_bets, all_combinations に ratio / probability あり）
- **verify details**: `run_verify(..., evaluation_mode="selected_bets")` の詳細（actual 等）

または

- **bets**: `[{"stake", "odds", "hit", "probability"?}, ...]` のリスト。`build_bet_list_from_verify(predictions, details)` で生成可能。

### 出力

- **bankroll_curve**: 各賭け後の資金のリスト
- **max_drawdown**: 最大ドローダウン（円）
- **sharpe_ratio**: 1 賭けあたりリターンの Sharpe（簡易）
- **profit_factor**: 総利益 / 総損失
- **bet_count**, **total_stake**, **total_payout**, **final_bankroll**, **roi_pct**

### 利用例

```python
from kyotei_predictor.betting.bankroll_simulation import (
    build_bet_list_from_verify,
    simulate_bankroll,
)

bets = build_bet_list_from_verify(predictions, verify_details, fixed_stake=100.0)
result_fixed = simulate_bankroll(bets, initial_bankroll=100_000, bet_sizing="fixed")
result_kelly = simulate_bankroll(bets, initial_bankroll=100_000, bet_sizing="kelly_half")
```

---

## 5. Rolling validation 拡張（EV 戦略比較）

### 条件

- train 15日 / test 7日 / 4 window（従来と同じ）
- calibration = sigmoid
- 戦略: B top_n=3, B top_n=5 EV>1.10, B top_n=5 EV>1.15

### 比較軸

- EV threshold（1.10, 1.15）
- bet sizing（fixed, kelly_half）

### 出力指標

- ROI（%）
- max_drawdown
- Sharpe ratio
- profit factor

### 実行方法

```bash
PYTHONPATH=. python3 kyotei_predictor/tools/rolling_ev_strategy_compare.py
```

### 結果保存

- **logs/rolling_ev_strategy_compare.json**

---

## 6. 最終推奨戦略（確定）

EV スイープと rolling EV 比較の実結果に基づき、以下を主戦略として固定する。

### 主戦略（本番デフォルト）

| 項目 | 値 | 根拠 |
|------|-----|------|
| model | baseline B | 既存方針 |
| calibration | sigmoid | 既存方針・確率補正 |
| top_n | 5 | EV 選定の候補数 |
| EV threshold | **1.15** | スイープで損失最小（1 window）。rolling で EV>1.15 が mean_roi 最良。 |
| bet sizing | **fixed** | rolling で fixed の方が max_drawdown が小さく運用しやすい。 |

- **選定ロジック**: B top_n=5 のうち、expected_roi >= 1.15 の組み合わせのみ購入。1 点 100 円固定。

### 代替戦略（オプション）

- **やや多点・閾値ゆるめ**: EV threshold 1.10。bet_count を増やしたい場合。
- **リスク抑制**: 同じく EV 1.15 + fixed。閾値を 1.15 に固定し、bet sizing は kelly にしない（fixed のまま）。
- **比較研究用**: kelly_half はドローダウンが大きいため本番非推奨。実験時のみ利用。

### 選定の基準（どういう判断をしたか）

1. **EV 閾値**: スイープで 1.02〜1.20 を比較。1 window では全閾値マイナスだが、相対的に 1.15 が最も損失が小さく、1.20 は悪化。bet_count も 689 で十分なため 1.15 を採用。
2. **bet sizing**: rolling で fixed と kelly_half を比較。fixed の方が max_drawdown が約 1/3 以下で、Sharpe も同程度かやや良いため fixed を採用。
3. **top_n=5**: 従来の rolling / calibration 比較で使用してきた値のまま。
4. **calibration=sigmoid**: 既存の暫定推奨を維持。

### 再検証結果（主戦略 4 window）

同一条件で主戦略のみ 4 window を再実行した結果。保存先: **logs/strategy_b_validation_windows.json**

| 戦略 | mean_roi_pct | positive_roi_windows | total_bet | total_profit |
|------|--------------|----------------------|-----------|--------------|
| B top_n=5 EV>1.15 | -21.94 | 1/4 | 238,700 | -55,670 |
| B top_n=5 EV>1.10 | -23.88 | 1/4 | 244,100 | -61,070 |

- EV>1.15 の方が平均 ROI・利益ともマシ。直近実行では 4 中 1 window のみプラス。
- 過去の calibration 比較（同一 4 window）では sigmoid で平均 ROI がプラスだったが、再実行時期・乱数・データで結果が変わりうる。差分は **docs/STRATEGY_B_CONDITION_DIFF.md** 参照。

### 現時点での採用理由と保留事項

- **採用理由**: スイープ・rolling 比較で「EV 1.15 + fixed」が相対的に最良。config/CLI デフォルトをこの主戦略に合わせて運用しやすくした。
- **保留事項**: 直近の再検証では 4 window 平均がマイナス。過去のプラス結果は再現していない。主戦略は「相対的に最良」として採用するが、**定期的に strategy_b_validation_windows や rolling_validation_calibration を再実行**し、平均 ROI や正の ROI window 数を追う。再現性が悪い場合はデータ固定・シード固定を検討する。

### 推奨戦略での実行方法

- **予測（主戦略）**: config デフォルトが top_n_ev, top_n=5, ev_threshold=1.15 のため、以下で主戦略の買い目が付与される。
  ```bash
  python -m kyotei_predictor.cli.baseline_predict --predict-date 2024-06-20 --data-dir path/to/data --include-selected-bets
  ```
- **閾値・戦略の上書き**: `--strategy top_n_ev --top-n 5 --ev-threshold 1.10` のように指定すれば config を上書き可能。
