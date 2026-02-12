# 学習→予測サイクル 実施結果と改善点

**実施日**: 2025-02-12  
**使用データ**: リポジトリ内 `kyotei_predictor/data/test_raw`（2024-05-01、84ペア）

---

## 1. 実施したサイクル

| ステップ | コマンド例 | 結果 |
|----------|------------|------|
| **学習** | `py -3 -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir kyotei_predictor/data/test_raw --year-month 2024-05 --minimal --n-trials 1` | ✅ 成功（約60分、最良スコア 4.12、`optuna_models/graduated_reward_best/best_model.zip` 保存） |
| **予測** | `py -3 -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --venues TODA,KIRYU --data-dir kyotei_predictor/data/test_raw` | ✅ 成功（24レース予測、`outputs/predictions_2024-05-01.json` 保存） |

**対応した変更**: 予測ツールに `--data-dir` を追加。リポジトリ内の `test_raw` を指定して予測可能にした。

---

## 2. 改善点一覧

### 2.1 必須・推奨（動かすために必要だった／あるとよいもの）

| # | 改善点 | 内容 | 状態 |
|---|--------|------|------|
| 1 | **予測のデータディレクトリ指定** | 予測が `data/raw` のみ参照しており、リポジトリ内の `test_raw` で予測できなかった。`--data-dir` を追加し、学習と同じデータソースで予測できるようにする。 | ✅ 対応済み（`--data-dir` 追加） |
| 2 | **依存関係の揃え方** | 予測実行時に `metaboatrace` や `requests` がなくエラーになった。学習は別環境（venv）で動いていた可能性。`requirements.txt` を 1 セットにし、学習・予測を同じ venv で実行する手順をドキュメントに明記する。 | ✅ 対応済み（LEARNING_AND_PREDICTION_STATUS に「同じ venv で」追記） |
| 3 | **requirements.txt のエンコーディング** | `pip install -r requirements.txt` で Windows の cp932 解釈時に UnicodeDecodeError が出た。ファイルを UTF-8（BOM なし）で保存する。 | ✅ 対応済み（UTF-8 BOM なしで保存） |

### 2.2 ログ・実行環境（Windows）

| # | 改善点 | 内容 | 状態 |
|---|--------|------|------|
| 4 | **予測ツールのログエラー** | Windows で `sys.stdout` を codecs でラップした結果、logging の StreamHandler が「raw stream has been detached」で失敗している。ログはファイルには出ているが、コンソール出力で例外が多発。対策: 標準出力の差し替えをやめる、または logging の設定を「ファイルのみ」にする／StreamHandler を付けない。 | ✅ 対応済み（Windows では StreamHandler を付けずファイルのみ、stdout の detach を廃止） |
| 5 | **学習ログの文字化け** | 学習時のコンソールメッセージが環境によって文字化けしている（例: 「使用するデータディレクトリ」が別表記になる）。UTF-8 出力の統一や、ログをファイルに出すだけにするなどの検討。 | ✅ 対応済み（重要メッセージは UTF-8 ログファイルへ、コンソールは英語サマリーのみ） |

### 2.3 運用・ドキュメント

| # | 改善点 | 内容 | 状態 |
|---|--------|------|------|
| 6 | **学習→予測のワンライナー** | リポジトリ内データで「学習→予測」を一気に回すスクリプトやバッチを 1 本用意する（例: `run_learning_prediction_cycle.bat` で `--minimal` 学習のあと `--data-dir test_raw` で予測）。 | ✅ 対応済み（`run_learning_prediction_cycle.bat` 追加） |
| 7 | **LEARNING_AND_PREDICTION_STATUS の更新** | `--data-dir` の説明と、リポジトリ内データで回す手順（test_raw を使う場合）を追記する。 | ✅ 対応済み（環境・venv・データペアの節を追加） |
| 8 | **学習データの前提** | 学習は `race_data_*` と `odds_data_*` の**ペア**が必須。片方だけや日付・会場の不一致があるとエピソードが作れずエラーになる。データ取得バッチやドキュメントで「ペアで揃える」ことを明記する。 | ✅ 対応済み（2.4 節でペア必須を明記） |

### 2.4 任意（中長期）

| # | 改善点 | 内容 | 状態 |
|---|--------|------|------|
| 9 | **ImprovementConfigManager の扱い** | 学習開始時に "ImprovementConfigManager not available, using default values" が出る。config の読み込みパスや実行ディレクトリの影響の可能性。必要ならパス解決を整理する。 | ✅ 対応済み（optimize_graduated_reward のインポートを kyotei_predictor.config に変更） |
| 10 | **学習ログ量** | 最小 1 試行でもログが非常に多い（8万行超）。本番では DEBUG を減らす、またはファイルのみにし、コンソールはサマリーだけにする。 | ✅ 対応済み（詳細は DEBUG でファイルのみ、コンソールは英語サマリー、ログは kyotei_predictor/logs/optimize_graduated_reward_YYYYMMDD.log） |
| 11 | **予測結果の検証** | 学習データと同じ日・会場で予測した結果について、簡易的な「的中率」や「期待値」の集計スクリプトがあると、サイクル改善の指標にしやすい。 | ✅ 対応済み（verify_predictions.py: 1位/Top3/10/20 的中率・回収率を集計） |

---

## 3. 今回の修正（コード）

- **prediction_tool.py**
  - `PredictionTool.__init__` に `data_dir` を追加。
  - `get_race_data_paths` で `self.data_dir` があればそれを参照（相対パスはプロジェクトルート基準で解決）。
  - コマンドライン引数に `--data-dir` を追加。
- これにより、リポジトリ内の `kyotei_predictor/data/test_raw` を指定して予測できるようになった。

### 3.2 改善点対応（上記に続けて実施）

- **requirements.txt**: UTF-8（BOM なし）で保存し直し、Windows で `pip install -r requirements.txt` が通るようにした。
- **prediction_tool.py**: Windows では標準出力の detach を廃止し、`setup_logging` で StreamHandler を追加せず FileHandler のみにした（「raw stream has been detached」回避）。
- **LEARNING_AND_PREDICTION_STATUS.md**: 2.4「学習データの前提（ペア必須）」、2.5「環境・依存関係（同じ venv、pip install -r requirements.txt）」を追加。
- **run_learning_prediction_cycle.bat**: 学習（--minimal --n-trials 1, test_raw）→ 予測（2024-05-01, test_raw）を一括実行するバッチを追加。

### 3.3 続きの改善点対応（#5, #9, #10, #11）

- **#5 学習ログの文字化け**: 学習スクリプトで UTF-8 のログファイル（`kyotei_predictor/logs/optimize_graduated_reward_YYYYMMDD.log`）を追加。重要メッセージはログファイルに日本語で出力し、コンソールは英語サマリーのみにして文字化けを回避。
- **#9 ImprovementConfigManager**: `optimize_graduated_reward.py` のインポートを `from kyotei_predictor.config.improvement_config_manager` に変更し、実行ディレクトリに依存しないようにした。
- **#10 学習ログ量**: 詳細な `print` を `_log_debug()`（DEBUG レベル・ファイルのみ）に変更。コンソールは「Data dir」「Year-month」「Optimization start」「Best trial」等の短い英語メッセージのみ。
- **#11 予測結果の検証**: `kyotei_predictor/tools/verify_predictions.py` を追加。予測 JSON と `race_data_*` の着順を照合し、1位/Top3/10/20 的中率と回収率（ROI）を表示。`--prediction` / `--data-dir` / `--output` / `--verbose` 対応。

---

## 4. 再現手順（リポジトリ内データで学習→予測）

1. **プロジェクトルート**（内側の `kyotei_Prediction/`）に移動。
2. **学習**（最小 1 試行）:
   ```bat
   py -3 -m kyotei_predictor.tools.optimization.optimize_graduated_reward --data-dir kyotei_predictor/data/test_raw --year-month 2024-05 --minimal --n-trials 1
   ```
3. **予測**（TODA・KIRYU、test_raw を参照）:
   ```bat
   py -3 -m kyotei_predictor.tools.prediction_tool --predict-date 2024-05-01 --venues TODA,KIRYU --data-dir kyotei_predictor/data/test_raw
   ```
4. 結果: `outputs/predictions_2024-05-01.json` を確認。

---

**作成日**: 2025-02-12
