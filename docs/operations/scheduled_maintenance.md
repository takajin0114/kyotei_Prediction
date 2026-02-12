# 一括バッチスケジューラ化運用ガイド

**最終更新日**: 2025-07-11  
**バージョン**: 1.0

---

## 📋 概要

本ガイドでは、一括バッチ（`run_data_maintenance.py`）のスケジューラ化による自動運用について詳しく説明します。

### 目的
- データ取得・欠損再取得・品質チェックを毎日自動実行
- 運用ミスや手動忘れを防ぐ
- データ品質の継続的な監視・改善

---

## 🚀 推奨運用フロー

### 基本フロー
1. **毎日深夜2時**に前日分のデータメンテナンスを自動実行
2. **バッチ完了後**に品質チェックを自動実行
3. **問題があればアラート通知**（メール等）
4. **実行履歴を記録**し、定期レビュー

### 実行内容
- データ取得（全会場・前日分）
- 欠損データの再取得
- データ品質チェック
- 品質レポートの生成・保存

---

## 🛠️ スケジューラ設定方法

### 方法1: scheduleライブラリ（推奨）

#### インストール
```bash
pip install schedule
```

#### 実行
```bash
# 毎日深夜2時に自動実行
python -m kyotei_predictor.tools.scheduled_data_maintenance --schedule --time 02:00

# 今すぐ実行（テスト用）
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now

# テスト実行（2日前のデータでテスト）
python -m kyotei_predictor.tools.scheduled_data_maintenance --test-run
```

### 方法2: Windowsタスクスケジューラ

#### 設定手順
1. **タスクスケジューラ**を開く
2. **基本タスクの作成**を選択
3. **名前**: "kyotei_data_maintenance"
4. **トリガー**: 毎日、開始時刻 02:00
5. **操作**: プログラムの開始
6. **プログラム**: `python`
7. **引数**: `-m kyotei_predictor.tools.scheduled_data_maintenance --run-now`
8. **開始場所**: プロジェクトルートディレクトリ

#### バッチファイル作成例
```batch
@echo off
cd /d D:\git\kyotei_Prediction
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now
```

### 方法3: cron（Linux/Mac）

#### crontab設定例
```bash
# 毎日深夜2時に実行
0 2 * * * cd /path/to/kyotei_Prediction && python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now

# ログ出力も含める場合
0 2 * * * cd /path/to/kyotei_Prediction && python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now >> /var/log/kyotei_maintenance.log 2>&1
```

---

## 📊 実行結果の確認

### ログファイル
- **実行ログ**: `kyotei_predictor/logs/scheduled_maintenance_YYYYMMDD.log`
- **履歴**: `outputs/scheduled_maintenance_history.json`
- **品質レポート**: `outputs/quality_report_YYYY-MM-DD.json`

### 確認コマンド
```bash
# 最新の実行履歴を確認
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now

# 特定日付の品質レポートを確認
python -m kyotei_predictor.tools.data_quality_checker --date 2024-01-01
```

---

## ⚠️ トラブルシューティング

### よくある問題と対処法

#### 1. スケジューラが起動しない
**原因**: Python環境やパスの問題
**対処法**:
```bash
# 絶対パスで実行
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now

# 環境確認
python --version
pip list | grep schedule
```

#### 2. データ取得に失敗
**原因**: ネットワーク問題、サイト変更
**対処法**:
- ログファイルで詳細エラーを確認
- 手動で再実行して状況確認
- 必要に応じてスクリプト修正

#### 3. 品質チェックで問題検出
**原因**: データ欠損、異常値
**対処法**:
- 品質レポートで詳細確認
- 欠損データの手動再取得
- データソースの状況確認

### 緊急時の対応

#### スケジューラ停止
```bash
# Ctrl+C で停止（scheduleライブラリ使用時）
# またはタスクスケジューラで無効化
```

#### 手動実行
```bash
# 特定日付の手動実行
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now --start-date 2024-01-01 --end-date 2024-01-01

# 全期間の手動実行
python -m kyotei_predictor.tools.batch.run_data_maintenance --start-date 2024-01-01 --end-date 2024-01-31 --stadiums ALL
```

---

## 📈 運用監視・改善

### 定期チェック項目
- **日次**: 実行ログの確認
- **週次**: 品質レポートのレビュー
- **月次**: 実行履歴の分析・改善

### 監視指標
- 実行成功率
- 実行時間
- データ品質スコア
- エラー発生率

### 改善サイクル
1. **現状把握**: ログ・レポートの分析
2. **問題特定**: エラー・品質問題の特定
3. **対策実施**: スクリプト修正・設定調整
4. **効果確認**: 改善後の監視

---

## 🔧 カスタマイズ・拡張

### アラート設定
`kyotei_predictor/config/alert_config.json` でメール通知を設定可能

```json
{
  "email_enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_emails": ["admin@example.com"],
  "alert_threshold": "warning"
}
```

### 実行時刻の変更
```bash
# 朝9時に実行
python -m kyotei_predictor.tools.scheduled_data_maintenance --schedule --time 09:00

# 複数回実行（例：朝9時と夜9時）
# スクリプトを修正して複数スケジュールを設定
```

### 対象会場の変更
```bash
# 特定会場のみ
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now --stadiums KIRYU,TODA

# 全会場（デフォルト）
python -m kyotei_predictor.tools.scheduled_data_maintenance --run-now --stadiums ALL
```

---

## 📚 関連ドキュメント

- [データ取得運用ガイド](data_acquisition.md) - データ取得バッチの実行手順と運用ノウハウ
- [全体状況サマリー](../CURRENT_STATUS_SUMMARY.md) - バッチ運用を含むプロジェクト全体の現状
- [予測精度向上TODO](../PREDICTION_ACCURACY_IMPROVEMENT_TODO.md) - 今後の改善タスク

---

## 📝 更新履歴

- **2025-07-11**: 初版作成、スケジューラ化運用ガイド完成 