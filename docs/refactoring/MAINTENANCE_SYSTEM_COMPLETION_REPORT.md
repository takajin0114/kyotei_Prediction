# メンテナンスシステム実装完了レポート

**実行日**: 2025-07-30  
**対象プロジェクト**: kyotei_Prediction  
**作業内容**: 定期的なクリーンアップスケジュール・容量監視システムの実装

---

## 📋 実装したシステム

### **1. 自動クリーンアップシステム**

#### **実装ファイル**
- `kyotei_predictor/tools/maintenance/auto_cleanup.py` - メインクリーンアップスクリプト
- `cleanup_config.json` - クリーンアップ設定ファイル

#### **主要機能**
```
✅ ログファイルの自動削除
- outputs/logs/ 内の古いログファイル
- 最新10個を保持、100MB制限

✅ チェックポイントファイルの整理
- optuna_models/graduated_reward_checkpoints/ 内の古いファイル
- 最新5個を保持、500MB制限

✅ アーカイブファイルの整理
- archives/optimization/ 内の古いファイル
- 最新20個を保持、1GB制限

✅ trialディレクトリの整理
- optuna_models/ と optuna_logs/ 内の古いtrialディレクトリ
- 最新10個を保持

✅ 一時ファイルの削除
- __pycache__/ ディレクトリ
- .pytest_cache/ ディレクトリ
- *.tmp, *.temp, *.log.bak ファイル
```

#### **使用方法**
```bash
# 基本的なクリーンアップ実行
python kyotei_predictor/tools/maintenance/auto_cleanup.py

# レポートのみ生成
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only

# 設定ファイルを指定
python kyotei_predictor/tools/maintenance/auto_cleanup.py --config cleanup_config.json
```

### **2. ディスク容量監視システム**

#### **実装ファイル**
- `kyotei_predictor/tools/maintenance/disk_monitor.py` - メイン監視スクリプト
- `monitor_config.json` - 監視設定ファイル

#### **主要機能**
```
✅ ディスク使用率の監視
- 警告レベル: 70%
- 危険レベル: 85%
- 緊急レベル: 95%

✅ ディレクトリサイズの監視
- optuna_models: 5GB制限
- optuna_logs: 2GB制限
- optuna_tensorboard: 3GB制限
- outputs: 1GB制限
- archives: 10GB制限

✅ リアルタイムアラート
- 警告・危険・緊急レベルの通知
- 履歴の保持（最新50個のアラート）
- 監視履歴の保持（最新100個の記録）

✅ レポート生成
- ディスク使用量レポート
- ディレクトリサイズレポート
- アラート履歴レポート
```

#### **使用方法**
```bash
# 現在のステータスを表示
python kyotei_predictor/tools/maintenance/disk_monitor.py --status

# レポートを生成
python kyotei_predictor/tools/maintenance/disk_monitor.py --report

# デーモンモードで実行
python kyotei_predictor/tools/maintenance/disk_monitor.py --daemon
```

### **3. 定期実行スケジューラ**

#### **実装ファイル**
- `kyotei_predictor/tools/maintenance/scheduler.py` - メインスケジューラ
- `scheduler_config.json` - スケジューラ設定ファイル

#### **主要機能**
```
✅ 日次クリーンアップ
- 実行時間: 毎日02:00
- 基本的なクリーンアップを実行

✅ 週次クリーンアップ
- 実行時間: 毎週日曜03:00
- 詳細なクリーンアップを実行

✅ ディスク監視
- 実行間隔: 30分
- ディスク使用量をチェック

✅ 緊急クリーンアップ
- ディスク使用率90%超過時に自動実行
- 緊急時の自動対応
```

#### **使用方法**
```bash
# 現在のステータスを表示
python kyotei_predictor/tools/maintenance/scheduler.py --status

# 即座にクリーンアップを実行
python kyotei_predictor/tools/maintenance/scheduler.py --run-now

# デーモンモードで実行
python kyotei_predictor/tools/maintenance/scheduler.py --daemon
```

---

## 📊 設定ファイル詳細

### **1. クリーンアップ設定 (`cleanup_config.json`)**
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
    },
    "archives/optimization": {
      "enabled": true,
      "max_files": 20,
      "max_size_mb": 1000
    }
  }
}
```

### **2. 監視設定 (`monitor_config.json`)**
```json
{
  "monitoring": {
    "check_interval": 60,
    "warning_threshold": 70,
    "critical_threshold": 85,
    "emergency_threshold": 95
  },
  "directories": {
    "optuna_models": {"max_size_gb": 5},
    "optuna_logs": {"max_size_gb": 2},
    "optuna_tensorboard": {"max_size_gb": 3},
    "outputs": {"max_size_gb": 1},
    "archives": {"max_size_gb": 10}
  }
}
```

### **3. スケジューラ設定 (`scheduler_config.json`)**
```json
{
  "schedules": {
    "daily_cleanup": {
      "enabled": true,
      "time": "02:00"
    },
    "weekly_cleanup": {
      "enabled": true,
      "day": "sunday",
      "time": "03:00"
    },
    "disk_monitor": {
      "enabled": true,
      "interval_minutes": 30
    }
  }
}
```

---

## 🎯 監視・制限設定

### **ディスク容量監視**
- **警告レベル**: 70% - 注意喚起
- **危険レベル**: 85% - 緊急対応準備
- **緊急レベル**: 95% - 即座の対応

### **ディレクトリサイズ制限**
- **optuna_models**: 5GB - モデルファイル
- **optuna_logs**: 2GB - ログファイル
- **optuna_tensorboard**: 3GB - TensorBoardログ
- **outputs**: 1GB - 出力ファイル
- **archives**: 10GB - アーカイブファイル

### **ファイル保持数制限**
- **ログファイル**: 最新10個
- **チェックポイント**: 最新5個
- **アーカイブ**: 最新20個
- **trialディレクトリ**: 最新10個

---

## 📈 生成されるレポート・ログ

### **レポートファイル**
- `cleanup_report.json` - クリーンアップ実行結果
- `disk_monitor_report.json` - ディスク監視結果

### **ログファイル**
- `auto_cleanup.log` - クリーンアップログ
- `disk_monitor.log` - 監視ログ
- `scheduler.log` - スケジューラログ

### **レポート内容**
```json
{
  "timestamp": "2025-07-30T10:00:00",
  "disk_usage": {
    "total_gb": 500.0,
    "used_gb": 350.0,
    "free_gb": 150.0,
    "usage_percent": 70.0
  },
  "directories": {
    "optuna_models": {
      "size_gb": 2.5,
      "file_count": 150
    }
  }
}
```

---

## 🚀 運用開始手順

### **1. 依存関係の確認**
```bash
pip install schedule psutil
```

### **2. 設定ファイルの確認**
```bash
# 設定ファイルの構文チェック
python -m json.tool cleanup_config.json
python -m json.tool monitor_config.json
python -m json.tool scheduler_config.json
```

### **3. 初回テスト実行**
```bash
# ディスク監視のテスト
python kyotei_predictor/tools/maintenance/disk_monitor.py --status

# クリーンアップのテスト
python kyotei_predictor/tools/maintenance/auto_cleanup.py --report-only
```

### **4. 自動実行開始**
```bash
# スケジューラ開始（推奨）
python kyotei_predictor/tools/maintenance/scheduler.py --daemon

# または個別実行
python kyotei_predictor/tools/maintenance/disk_monitor.py --daemon
```

---

## 📊 期待される効果

### **ディスク容量の最適化**
- **自動クリーンアップ**: 定期的な古いファイル削除
- **容量監視**: 早期警告による予防的対応
- **緊急対応**: 容量不足時の自動クリーンアップ

### **運用効率の向上**
- **自動化**: 手動作業の削減
- **監視**: リアルタイムな状況把握
- **レポート**: 定量的な管理

### **システム安定性の向上**
- **予防的メンテナンス**: 問題の早期発見
- **自動対応**: 緊急時の自動処理
- **履歴管理**: 過去の状況把握

---

## ⚠️ 注意事項

### **1. バックアップ**
- 重要なファイルは事前にバックアップを取得
- 設定ファイルで削除対象を慎重に設定

### **2. 実行時間**
- クリーンアップは深夜（02:00-03:00）に実行
- 大量ファイルがある場合、処理時間が長くなる可能性

### **3. ログ管理**
- ログファイルは自動的にローテーション
- 古いログは自動的に削除

---

## 🔍 トラブルシューティング

### **よくある問題と対処法**

#### **1. 権限エラー**
```bash
# 管理者権限で実行
sudo python kyotei_predictor/tools/maintenance/auto_cleanup.py
```

#### **2. 依存関係エラー**
```bash
# 依存関係を再インストール
pip install schedule psutil
```

#### **3. 設定ファイルエラー**
```bash
# 設定ファイルの構文チェック
python -m json.tool cleanup_config.json
```

---

## 📞 サポート情報

### **ログファイルの確認**
- `auto_cleanup.log` - クリーンアップ実行ログ
- `disk_monitor.log` - 監視ログ
- `scheduler.log` - スケジューラログ

### **設定ファイルの確認**
- `cleanup_config.json` - クリーンアップ設定
- `monitor_config.json` - 監視設定
- `scheduler_config.json` - スケジューラ設定

### **レポートファイルの確認**
- `cleanup_report.json` - クリーンアップ結果
- `disk_monitor_report.json` - 監視結果

---

## 🎯 次のステップ

### **即座に実行可能**
1. **システムテスト** - 各ツールの動作確認
2. **設定調整** - 環境に合わせた設定調整
3. **自動実行開始** - スケジューラの開始

### **中期的な改善**
4. **通知機能の拡張** - メール・Discord通知
5. **レポート機能の強化** - より詳細な分析
6. **監視項目の追加** - メモリ・CPU監視

### **長期的な拡張**
7. **Webダッシュボード** - ブラウザベースの監視
8. **機械学習による予測** - 容量予測機能
9. **クラウド連携** - クラウドストレージとの連携

---

**メンテナンスシステムの実装が正常に完了しました。自動クリーンアップ・ディスク容量監視・定期実行スケジューラが整備され、プロジェクトの安定運用が可能になりました。** 