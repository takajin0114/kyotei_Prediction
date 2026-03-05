# 実行確認の手順

プロジェクトルート（`kyotei_Prediction/`）で以下を実行する。

---

## 1. 環境準備（初回のみ）

```bash
# 仮想環境作成
python3 -m venv .venv

# 有効化（macOS/Linux）
source .venv/bin/activate

# 依存インストール
pip install -r requirements.txt
```

Windows の場合は `.venv\Scripts\activate`。

---

## 2. テストで実行確認

```bash
# メイン処理のテストのみ（短時間）
python -m pytest kyotei_predictor/tests/test_prediction_engine_main.py kyotei_predictor/tests/test_data_integration_main.py kyotei_predictor/tests/test_prediction_tool_main.py -v --tb=short

# 全体（時間かかる場合あり）
python -m pytest kyotei_predictor/tests/ -v --tb=short
```

---

## 3. 学習スクリプトの実行確認

### 3.1 ヘルプ表示（DB 対応の引数確認）

```bash
python -m kyotei_predictor.tools.batch.train_with_graduated_reward --help
```

`--data-source`, `--db-path`, `--year-month` が表示されれば OK。

### 3.2 ごく短い学習（file モード・数十秒で終わる）

```bash
python -m kyotei_predictor.tools.batch.train_with_graduated_reward --total-timesteps 500
```

※ `kyotei_predictor/data/raw` にレース JSON が無い場合は「ペア 0」で終了するかエラーになる。その場合は 3.3 の DB モードを試す。

### 3.3 DB モードで短い学習（DB がある場合）

```bash
python -m kyotei_predictor.tools.batch.train_with_graduated_reward --data-source db --year-month 2025-01 --total-timesteps 500
```

※ `kyotei_predictor/data/kyotei_races.sqlite` が存在し、指定した年月のデータが入っている必要あり。

---

## 4. 最適化スクリプトの実行確認

```bash
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --help
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-source db --year-month 2025-01 --fast-mode --n-trials 2
```

※ 2 トライアルだけなので数分で終わる想定。

---

## 5. まとめ

| 確認項目 | コマンド |
|----------|----------|
| テスト（メイン） | `pytest kyotei_predictor/tests/test_prediction_engine_main.py kyotei_predictor/tests/test_data_integration_main.py kyotei_predictor/tests/test_prediction_tool_main.py -v` |
| train --help | `python -m kyotei_predictor.tools.batch.train_with_graduated_reward --help` |
| train 短い実行（file） | `python -m kyotei_predictor.tools.batch.train_with_graduated_reward --total-timesteps 500` |
| train 短い実行（db） | `python -m kyotei_predictor.tools.batch.train_with_graduated_reward --data-source db --year-month 2025-01 --total-timesteps 500` |
| optimize 短い実行 | `python -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-source db --year-month 2025-01 --fast-mode --n-trials 2` |
