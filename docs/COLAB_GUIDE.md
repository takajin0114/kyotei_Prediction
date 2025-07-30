# Google Colab 環境での強化学習実行ガイド

**最終更新日**: 2025-07-30  
**対象環境**: Google Colab  
**目的**: 環境依存をなくし、Colab環境で強化学習を実行

---

## 🚀 クイックスタート

### 1. リポジトリのクローン

```python
# リポジトリをクローン
!git clone https://github.com/your-username/kyotei_Prediction.git
%cd kyotei_Prediction
```

### 2. 環境セットアップ

```python
# セットアップスクリプトを実行
!python colab_setup.py
```

### 3. 強化学習の実行

```python
# 統合最適化スクリプトで強化学習を実行
!python kyotei_predictor/tools/optimization/unified_optimizer.py \
    --type graduated_reward \
    --project-root /content/kyotei_Prediction \
    --n-trials 50 \
    --timeout 1800
```

---

## 📋 環境依存の解決

### **絶対パスの動的解決**

- **問題**: スクリプトが絶対パスに依存していた
- **解決**: 環境を自動検出し、適切なパスを動的に決定
- **実装**: `/content/` パスの検出によるColab環境の自動認識

### **ディスク容量監視の改善**

- **問題**: Colab環境ではディスク容量チェックが失敗する可能性
- **解決**: 例外処理を追加し、エラー時も処理を継続
- **実装**: `try-except` ブロックによる堅牢なエラーハンドリング

### **設定ファイルの環境対応**

- **問題**: ローカル環境用の設定がColab環境に適していない
- **解決**: Colab環境用の最適化された設定を自動生成
- **実装**: 容量制限を厳しく設定し、効率的なリソース管理

---

## 🔧 詳細設定

### **メンテナンス設定**

```json
{
  "cleanup_config.json": {
    "max_disk_usage_percent": 90,
    "targets": {
      "outputs/logs": {
        "enabled": true,
        "max_files": 5,
        "max_size_mb": 50
      }
    }
  }
}
```

### **監視設定**

```json
{
  "monitor_config.json": {
    "monitoring": {
      "check_interval": 300,
      "warning_threshold": 80,
      "critical_threshold": 90
    }
  }
}
```

---

## 📊 使用方法

### **統合最適化スクリプト**

```python
# 段階的報酬最適化
!python kyotei_predictor/tools/optimization/unified_optimizer.py \
    --type graduated_reward \
    --project-root /content/kyotei_Prediction \
    --n-trials 100 \
    --timeout 3600

# シンプル最適化
!python kyotei_predictor/tools/optimization/unified_optimizer.py \
    --type simple \
    --project-root /content/kyotei_Prediction \
    --n-trials 20
```

### **メンテナンスツール**

```python
# ディスク容量監視
!python kyotei_predictor/tools/maintenance/disk_monitor.py \
    --project-root /content/kyotei_Prediction \
    --status

# 自動クリーンアップ
!python kyotei_predictor/tools/maintenance/auto_cleanup.py \
    --project-root /content/kyotei_Prediction \
    --report-only

# スケジューラ実行
!python kyotei_predictor/tools/maintenance/scheduler.py \
    --project-root /content/kyotei_Prediction \
    --daemon
```

---

## ⚠️ 注意事項

### **Colab環境の制限**

1. **ディスク容量**: 約80GBの制限
2. **セッション時間**: 12時間のタイムアウト
3. **メモリ制限**: 約12GBのRAM制限
4. **GPU制限**: 連続使用時間の制限

### **推奨設定**

- **試行回数**: 50-100回（長時間実行を避ける）
- **タイムアウト**: 1800秒（30分）
- **クリーンアップ**: 定期的な実行で容量管理
- **結果保存**: 重要な結果はGoogle Driveに保存

---

## 🔍 トラブルシューティング

### **よくある問題**

1. **パッケージインストールエラー**
   ```python
   !pip install --upgrade pip
   !python colab_setup.py
   ```

2. **ディスク容量不足**
   ```python
   !python kyotei_predictor/tools/maintenance/auto_cleanup.py \
       --project-root /content/kyotei_Prediction
   ```

3. **セッションタイムアウト**
   - 重要な結果をGoogle Driveに保存
   - 長時間の実行は分割して実行

### **デバッグ方法**

```python
# 環境情報の確認
import os
print(f"Colab環境: {'COLAB_GPU' in os.environ}")
print(f"現在のディレクトリ: {os.getcwd()}")

# プロジェクト構造の確認
!ls -la /content/kyotei_Prediction
```

---

## 📈 パフォーマンス最適化

### **Colab環境での最適化**

1. **GPU活用**: 強化学習でGPUを効率的に使用
2. **メモリ管理**: 大きなモデルは分割して処理
3. **ストレージ最適化**: 不要なファイルを定期的に削除
4. **並列処理**: 可能な限り並列処理を活用

### **推奨ワークフロー**

1. **セットアップ**: `colab_setup.py` で環境準備
2. **小規模テスト**: 少ない試行回数で動作確認
3. **本格実行**: 適切な設定で本格的な最適化
4. **結果保存**: 重要な結果をGoogle Driveに保存
5. **クリーンアップ**: 不要なファイルを削除

---

## 🎯 成果

### **環境依存の解決**

- ✅ 絶対パスの動的解決
- ✅ Colab環境の自動検出
- ✅ 堅牢なエラーハンドリング
- ✅ 環境対応設定ファイル

### **運用性の向上**

- ✅ 簡単なセットアップ
- ✅ 効率的なリソース管理
- ✅ 自動化されたメンテナンス
- ✅ 明確な使用方法

### **開発効率の向上**

- ✅ 環境に依存しないコード
- ✅ 統一されたインターフェース
- ✅ 詳細なドキュメント
- ✅ トラブルシューティングガイド

---

**Google Colab環境で強化学習を効率的に実行できるようになりました！** 