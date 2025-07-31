# 最適化関連ドキュメント

競艇予測モデルのハイパーパラメータ最適化に関するドキュメントを管理するディレクトリです。
**汎用的な月別データ対応システム**に対応しています。

## 📚 ドキュメント一覧

### [GENERIC_OPTIMIZATION_GUIDE.md](GENERIC_OPTIMIZATION_GUIDE.md) ⭐ **NEW**
汎用的な段階的報酬最適化の詳細ガイドです。
- 月別データ対応システムの使用方法
- インタラクティブ実行と一括実行
- 新しい月のデータ追加方法
- トラブルシューティング

### [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) ⭐ **UPDATED**
最適化実行の詳細ガイドです。
- 汎用システムに対応した実行方法
- 月別データ対応
- 設定オプション（テストモード、本番モード）
- 結果の確認方法
- トラブルシューティング

### [BATCH_EXECUTION_GUIDE.md](BATCH_EXECUTION_GUIDE.md)
最適化バッチ実行の包括的なガイドです。
- 実行方法（汎用スクリプト、直接実行、Pythonコード）
- 本番想定パラメータの詳細
- 実行状況監視方法
- トラブルシューティング
- 結果分析方法

### [CURRENT_STATUS.md](CURRENT_STATUS.md)
現在の最適化バッチ実行状況の詳細レポートです。
- 実行中の最適化状況
- 完了済み最適化履歴
- パフォーマンス指標
- 今後の予定

### [EXECUTION_EXAMPLES.md](EXECUTION_EXAMPLES.md)
具体的な実行例とサンプルコードです。
- 各種実行パターンの例
- エラー対処法
- ベストプラクティス

## 🚀 クイックスタート

### 基本的な実行

```bash
# 本番実行（推奨）
run_optimization_production_with_cleanup.bat

# インタラクティブ実行
run_optimization_with_setup_interactive.bat

# コマンドライン直接実行
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 --test-mode --n-trials 3
```

### 月別データでの実行

```bash
# 2024年1月データ（テストモード）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 --test-mode --n-trials 3

# 2024年1月データ（本番モード）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-01 --n-trials 50

# 2024年2月データ（今後追加予定）
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic \
    --data-month 2024-02 --n-trials 50
```

## 📊 最適化結果

### 保存場所

- **結果ファイル**: `optuna_results/graduated_reward_optimization_YYYYMM_YYYYMMDD_HHMMSS.json`
- **最良モデル**: `optuna_models/graduated_reward_best_YYYYMM/best_model.zip`
- **ログファイル**: `optuna_logs/trial_X/`
- **スタディファイル**: `optuna_studies/`

### 結果の確認

```python
import json

# 最新の結果を読み込み
with open('optuna_results/graduated_reward_optimization_202401_YYYYMMDD_HHMMSS.json', 'r') as f:
    results = json.load(f)

print(f"対象月: {results['data_month']}")
print(f"最良スコア: {results['best_trial']['value']}")
print(f"最良パラメータ: {results['best_trial']['params']}")
```

## 🔧 新しい月のデータを追加

### 1. データディレクトリの準備

```
kyotei_predictor/data/raw/2024-02/
├── race_data_2024-02-01_BIWAKO_R1.json
├── odds_data_2024-02-01_BIWAKO_R1.json
├── race_data_2024-02-01_BIWAKO_R2.json
├── odds_data_2024-02-01_BIWAKO_R2.json
└── ...
```

### 2. 実行スクリプトの更新

```python
# run_optimization_generic.py
months = [
    "2024-01",  # 1月
    "2024-02",  # 2月（新規追加）
    "2024-03",  # 3月（今後追加）
]

# run_optimization_batch.py
target_months = [
    "2024-01",  # 1月
    "2024-02",  # 2月（新規追加）
    # "2024-03",  # 3月（コメントアウトで無効化）
]
```

## 📋 実行モード

### テストモード
- **総ステップ数**: 1,000
- **評価エピソード数**: 10
- **実行時間**: 数分
- **用途**: 動作確認、パラメータ調整

### 本番モード
- **総ステップ数**: 100,000
- **評価エピソード数**: 2,000
- **実行時間**: 数時間
- **用途**: 本格的な最適化

## 🛠️ トラブルシューティング

### よくある問題

1. **データが見つからない**
   - データディレクトリの存在確認
   - ファイル名の形式確認

2. **メモリ不足**
   - テストモードで実行
   - データ量を制限

3. **的中率が0%**
   - テストモードでは想定通り
   - 本番モードで長時間学習

## 📈 パフォーマンス指標

### 理論的中率
- **三連複**: 約0.83%（1/120）
- **短時間学習**: 的中率向上は困難
- **長時間学習**: 的中率向上の可能性

### 評価指標
- **的中率**: 主要指標
- **平均報酬**: 補助指標
- **報酬の標準偏差**: 安定性指標

## 🔗 関連ファイル

### 実行スクリプト
- `run_optimization_generic.py` - インタラクティブ実行
- `run_optimization_batch.py` - 一括実行

### 最適化モジュール
- `kyotei_predictor/tools/optimization/optimize_graduated_reward_generic.py` - 汎用最適化モジュール

### 設定ファイル
- `kyotei_predictor/config/optuna_config.json` - Optuna設定

## 📝 更新履歴

- **2025-07-30**: 汎用的な月別データ対応システムを追加
- **2025-07-30**: GENERIC_OPTIMIZATION_GUIDE.mdを追加
- **2025-07-30**: OPTIMIZATION_GUIDE.mdを更新

---

**最終更新**: 2025-07-30  
**バージョン**: 2.0（汎用システム対応）

## 🐍 Python仮想環境・依存関係トラブル事例

### 事例
- 仮想環境(venv)のactivate時に「このシステムではスクリプトの実行が無効になっているため...」エラーが発生し、Pythonプロセスが即時終了。
- 最適化実行時にGymの非互換エラー（NumPy 2.0未対応）でプロセスが停止。

### 主な原因
- PowerShellの実行ポリシーが「Restricted」や「Undefined」だと、activateスクリプトが実行できない。
- Gym（旧版）はNumPy 2.0に非対応。

### 対策
- PowerShellで以下を実行し、一時的に実行ポリシーを緩和：
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .\venv\Scripts\activate
  ```
- 依存関係エラー時は、requirements.txtを再インストール：
  ```powershell
  pip install -r requirements.txt
  ```
- GymのNumPy 2.0非対応エラー時は、
  - (推奨) gymnasium への移行を検討
  - (暫定) NumPyを1系にダウングレード：
    ```powershell
    pip install numpy==1.26.4
    ```

### 備考
- 仮想環境の有効化・依存関係の再インストール・パス設定・主要モジュールのimport確認は、最適化実行前に必ず行うこと。