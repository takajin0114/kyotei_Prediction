# 主戦略 B の運用フロー

baseline B + sigmoid + top_n=5 + EV>=1.15 + fixed の再現手順と実行方法。**seed 固定で再現性を確保**する。

---

## 1. 主戦略の定義（固定）

| 項目 | 値 |
|------|-----|
| model | baseline B |
| calibration | sigmoid |
| strategy | top_n_ev |
| top_n | 5 |
| ev_threshold | 1.15 |
| bet_sizing | fixed（1 点 100 円） |
| evaluation_mode | selected_bets |
| seed | 未指定時は 42（学習・再検証で共通） |

---

## 1.1 再現手順（要約）

- **主戦略の 1 本実行**: `run_strategy_b` で実行（学習 → 予測 → 検証 → サマリ保存）。同一条件・同一 seed なら同じ結果になる。
- **再検証（複数 window）**: `strategy_b_validation_windows` で実行。4 window で seed=42 固定。

---

## 2. 1 本化フロー（学習 → 予測 → 検証 → サマリ）

1 回のコマンドで「指定期間で学習 → 指定日の予測 → 検証 → サマリ JSON 保存」まで実行する。

### CLI

```bash
python3 -m kyotei_predictor.cli.run_strategy_b \
  --train-start 2024-06-01 \
  --train-end 2024-06-15 \
  --predict-date 2024-06-16 \
  --data-dir kyotei_predictor/data/raw
```

- `--model-path`: 未指定時は出力先配下の `strategy_b_model.joblib`
- `--output`: 未指定時は data-dir の親の `outputs/strategy_b`
- `--seed`: 乱数シード。未指定時は 42。再現性用。
- `--save-summary-to`: サマリ JSON の任意の保存先

### 出力

- 予測 JSON: `output/predictions_strategy_b_<predict_date>.json`
- サマリ JSON: `output/strategy_b_summary_<predict_date>.json`（条件 + 検証 summary）
- モデル: `model_save_path` に保存

### サマリ JSON に保存される条件

`conditions` および `summary` に以下が含まれる。

- train_start, train_end, predict_date, data_dir
- model, calibration, top_n, ev_threshold, bet_sizing
- seed, race_count, selected_bets_count

### プログラムから呼ぶ場合

```python
from kyotei_predictor.application.run_strategy_b_usecase import run_strategy_b
from pathlib import Path

result = run_strategy_b(
    train_start="2024-06-01",
    train_end="2024-06-15",
    predict_date="2024-06-16",
    data_dir_raw=Path("kyotei_predictor/data/raw"),
    output_dir=Path("outputs/strategy_b"),
)
# result["summary"], result["conditions"], result["summary_path"]
```

---

## 3. 複数 window での再検証

主戦略のみで 4 window を回し、ROI・hit_rate・profit・mean_odds_placed 等を記録する。

```bash
PYTHONPATH=. python3 kyotei_predictor/tools/strategy_b_validation_windows.py
```

- **出力**: **logs/strategy_b_validation_windows.json**
- **内容**: seed（42 固定）、windows_detail（各 window に train_start, train_end, test_start, test_end、各戦略に roi_pct, hit_rate, total_bet, profit を保存）、aggregate_by_strategy（EV>1.15 / EV>1.10 の集計）

---

## 4. どの条件で比較したか

- **window**: 4 本（train 15日 / test 7日）
  - 06-01~06-15 → 06-16~06-22
  - 06-08~06-22 → 06-23~06-29
  - 06-15~06-29 → 06-30~07-06
  - 06-22~07-06 → 07-07~07-13
- **データ**: `data_dir_raw` 配下の月別ディレクトリ（YYYY-MM）の race_data_*.json / odds_data_*.json
- **検証**: run_verify(..., evaluation_mode="selected_bets")

---

## 5. 再現性（seed 固定）

- 学習時: `baseline_train_usecase.run_baseline_train(..., seed=42)` で `np.random.seed(seed)` と `random.seed(seed)` を設定し、`create_baseline_model(..., random_state=seed)` でモデルを生成。未指定時は seed=42。
- CLI: `baseline_train --seed 42`、`run_strategy_b --seed 42`。未指定時はデフォルト 42。
- 再検証: `strategy_b_validation_windows` は内部で seed=42 を渡して `run_one_window` を呼ぶ。同一データ・同一 seed なら同じ結果になる。

## 6. 差分の追い方

過去の「プラス結果」と直近の「マイナス結果」の条件差分は **docs/STRATEGY_B_CONDITION_DIFF.md** に整理している。再現するには同じスクリプトを再実行し、seed 固定により同一条件なら同じ結果を確認できる。
