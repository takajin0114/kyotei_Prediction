# logs/

実行時に生成されるログ・比較結果の出力先。**恒久成果物ではなく、コミット対象外**とする。

## 用途

- バッチ取得ログ（`batch_fetch_*.log`）
- 最適化・学習の tee 出力（`optimize_*.log`, `train_*.log`）
- 比較結果 JSON（`rolling_validation_*.json`, `ab_test_*.json` 等）

## 保存方針

- ローカル・CI で生成されたファイルはこのディレクトリに出力してよい。
- 長期保存が必要な結果は `outputs/` や実験ログ（`experiments/logs/`）にコピーする。

## Git 運用

- `logs/` は `.gitignore` で除外している。
- 本 README のみリポジトリに含め、中身のログファイルはコミットしない。
