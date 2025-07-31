# バッチ実行ガイド

## 概要

このガイドでは、複数月の一括最適化実行と自動クリーンアップ機能について説明します。

## 目次

1. [概要](#概要)
2. [実行方法](#実行方法)
3. [自動クリーンアップ機能](#自動クリーンアップ機能)
4. [設定オプション](#設定オプション)
5. [実行例](#実行例)
6. [トラブルシューティング](#トラブルシューティング)

---

## 実行方法

### 1. 基本的なバッチ実行

```bash
# 自動クリーンアップ付きバッチ実行
python run_optimization_batch.py

# 詳細レポート付きバッチ実行
python run_optimization_batch_with_cleanup.py
```

### 2. 実行フロー

1. **実行モード選択**
   - テストモード（短時間）
   - 本番モード（長時間）

2. **自動クリーンアップ設定**
   - 有効（推奨）
   - 無効

3. **最適化実行**
   - 各月の最適化を順次実行

4. **自動クリーンアップ**
   - 最適化完了後の古いファイル削除

5. **レポート生成**
   - 実行結果とクリーンアップ結果のレポート

---

## 自動クリーンアップ機能

### 1. 機能概要

最適化実行後に自動的に古いファイルを削除し、ディスク容量を管理します。

### 2. 削除対象

| ディレクトリ | 最大ファイル数 | 最大サイズ | 説明 |
|-------------|---------------|------------|------|
| `outputs/logs` | 10 | 100MB | ログファイル |
| `optuna_models/graduated_reward_checkpoints` | 5 | 500MB | モデルチェックポイント |
| `archives/optimization` | 20 | 1000MB | 最適化アーカイブ |
| `optuna_logs` | 15 | 200MB | Optunaログ |
| `optuna_tensorboard` | 10 | 300MB | TensorBoardログ |

### 3. 実行条件

- **成功時のみ**: 最適化が成功した場合のみ実行
- **手動選択**: ユーザーが有効/無効を選択可能
- **安全実行**: 設定ファイルで削除対象を制御

### 4. クリーンアップスクリプト

```bash
# 手動実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# レポートのみ生成
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only

# ドライラン（実際の削除は行わない）
python kyotei_predictor/tools/maintenance/auto_cleanup.py --dry-run
```

---

## 設定オプション

### 1. バッチ実行設定

#### 対象月の設定
```python
# run_optimization_batch.py
target_months = [
    "2024-01",  # 1月
    # "2024-02",  # 2月（コメントアウトで無効化）
    # "2024-03",  # 3月（コメントアウトで無効化）
]
```

#### 実行モード
- **テストモード**: 各月3試行、短時間実行
- **本番モード**: 各月50試行、長時間実行

### 2. クリーンアップ設定

#### 設定ファイル
```json
{
  "max_disk_usage_percent": 80,
  "targets": {
    "outputs/logs": {
      "enabled": true,
      "max_files": 10,
      "max_size_mb": 100
    },
    "optuna_models/graduated_reward_checkpoints": {
      "enabled": true,
      "max_files": 5,
      "max_size_mb": 500
    }
  }
}
```

#### ディスク監視
- **警告閾値**: 80%使用率
- **緊急クリーンアップ**: 90%使用率

---

## 実行例

### 例1: 基本的なバッチ実行

```bash
python run_optimization_batch.py
```

**実行フロー**:
1. 実行モード選択（テスト/本番）
2. 自動クリーンアップ設定（有効/無効）
3. 各月の最適化実行
4. 自動クリーンアップ実行
5. 実行時間の表示

### 例2: 詳細レポート付きバッチ実行

```bash
python run_optimization_batch_with_cleanup.py
```

**追加機能**:
- クリーンアップレポートの生成
- 詳細な実行ログ
- エラーハンドリングの強化

### 例3: 手動クリーンアップ

```bash
# クリーンアップのみ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# レポートのみ生成
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only
```

---

## トラブルシューティング

### 1. クリーンアップスクリプトが見つからない

**エラー**:
```
❌ クリーンアップスクリプトが見つかりません
```

**対処法**:
```bash
# スクリプトの存在確認
ls kyotei_predictor/tools/maintenance/auto_cleanup.py

# 手動でクリーンアップ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py
```

### 2. クリーンアップでエラーが発生

**対処法**:
```bash
# ドライランで確認
python kyotei_predictor/tools/maintenance/auto_cleanup.py --dry-run

# 設定ファイルの確認
cat kyotei_predictor/tools/maintenance/configs/cleanup_config.json
```

### 3. ディスク容量不足

**対処法**:
```bash
# 緊急クリーンアップ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# 手動で古いファイル削除
rm -rf optuna_logs/trial_*
rm -rf outputs/logs/*
```

---

## ベストプラクティス

### 1. 実行前の準備

- **ディスク容量確認**: 十分な空き容量を確保
- **設定確認**: クリーンアップ設定の確認
- **バックアップ**: 重要なファイルのバックアップ

### 2. 実行中の監視

- **ディスク使用率**: 定期的な容量確認
- **ログ確認**: クリーンアップログの確認
- **エラー監視**: エラーメッセージの確認

### 3. 実行後の確認

- **レポート確認**: クリーンアップレポートの確認
- **容量確認**: ディスク使用率の確認
- **ファイル確認**: 重要なファイルの存在確認

---

## 関連ファイル

### 実行スクリプト
- `run_optimization_batch.py` - 基本的なバッチ実行
- `run_optimization_batch_with_cleanup.py` - 詳細レポート付きバッチ実行

### クリーンアップ関連
- `kyotei_predictor/tools/maintenance/auto_cleanup.py` - 自動クリーンアップスクリプト
- `kyotei_predictor/tools/maintenance/configs/cleanup_config.json` - クリーンアップ設定

### 出力ファイル
- `cleanup_report.json` - クリーンアップ実行結果
- `auto_cleanup.log` - クリーンアップ実行ログ

---

**最終更新**: 2025-07-30  
**バージョン**: 2.0（自動クリーンアップ機能追加）