# バッチ実行ガイド

## 概要

競艇予測モデルの最適化を実行するためのバッチファイルの使用方法を説明します。

## 利用可能なバッチファイル

### 1. 本番実行用バッチファイル

#### `run_optimization_production_with_cleanup.bat`
**用途**: 本番環境での最適化実行（クリーンアップ付き）
- 仮想環境の有効化
- 依存関係の確認
- 指定データ月での最適化実行（50試行）
- 自動クリーンアップ実行

**実行方法**:
```cmd
run_optimization_production_with_cleanup.bat [DATA_MONTH]
```

**例**:
```cmd
run_optimization_production_with_cleanup.bat 2024-01
run_optimization_production_with_cleanup.bat 2024-02
```

#### `run_optimization_production_simple.bat`
**用途**: 簡易本番実行
- 基本的な最適化実行
- クリーンアップなし

**実行方法**:
```cmd
run_optimization_production_simple.bat [DATA_MONTH]
```

**例**:
```cmd
run_optimization_production_simple.bat 2024-01
run_optimization_production_simple.bat 2024-02
```

### 2. セットアップ付きバッチファイル

#### `run_optimization_with_setup_interactive.bat`
**用途**: インタラクティブな最適化実行
- 仮想環境の有効化
- 依存関係の確認
- データ月の選択
- 実行モードの選択（テスト/本番）

**実行方法**:
```cmd
run_optimization_with_setup_interactive.bat
```

#### `run_optimization_with_setup_cleanup.bat`
**用途**: セットアップ+クリーンアップ付き実行
- 仮想環境の有効化
- 依存関係の確認
- 最適化実行
- 自動クリーンアップ

**実行方法**:
```cmd
run_optimization_with_setup_cleanup.bat
```

#### `run_optimization_with_setup.bat`
**用途**: 基本的なセットアップ付き実行
- 仮想環境の有効化
- 依存関係の確認
- 最適化実行

**実行方法**:
```cmd
run_optimization_with_setup.bat
```

## 実行環境の準備

### 前提条件
1. Python 3.11以上がインストールされている
2. 仮想環境（venv）が作成されている
3. 必要な依存関係がインストールされている

### 仮想環境の作成（初回のみ）
```cmd
python -m venv venv
```

### 依存関係のインストール
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

## 実行手順

### 1. 本番実行（推奨）
```cmd
run_optimization_production_with_cleanup.bat 2024-01
```

### 2. インタラクティブ実行
```cmd
run_optimization_with_setup_interactive.bat
```

### 3. 手動実行
```cmd
venv\Scripts\activate
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-01 --n-trials 50
```

### 4. 他の月のデータで実行
```cmd
# 2024年2月データ
run_optimization_production_with_cleanup.bat 2024-02

# 2024年3月データ
run_optimization_production_with_cleanup.bat 2024-03

# 手動実行で他の月
python -m kyotei_predictor.tools.optimization.optimize_graduated_reward_generic --data-month 2024-02 --n-trials 50
```

## 実行結果

### 出力ディレクトリ
- `optuna_models/graduated_reward_best_202401/`: 最良モデル
- `optuna_studies/`: Optunaスタディデータベース
- `optuna_results/`: 最適化結果JSON
- `optuna_logs/`: ログファイル

### 結果ファイル
- `best_model.zip`: 最適化されたモデル
- `graduated_reward_optimization_202401_YYYYMMDD_HHMMSS.json`: 最適化結果

## トラブルシューティング

### よくある問題

#### 1. 仮想環境の有効化エラー
**症状**: `venv\Scripts\activate`でエラー
**解決方法**: PowerShellの実行ポリシーを変更
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

#### 2. 依存関係エラー
**症状**: モジュールインポートエラー
**解決方法**: 依存関係を再インストール
```cmd
pip install -r requirements.txt
```

#### 3. データが見つからないエラー
**症状**: "データペアが存在しません"エラー
**解決方法**: データディレクトリの確認
```
kyotei_predictor/data/raw/2024-01/
```

## パフォーマンス最適化

### 重複読み込み問題の解決
- 最適化モジュールで重複データ読み込みを排除
- 各trialでの読み込み時間を大幅短縮
- メモリ使用量を最適化

### 実行時間の目安
- **テストモード**: 2試行で約7秒
- **本番モード**: 50試行で約2分

## 注意事項

1. **実行前にデータの確認**: 2024-01データが存在することを確認
2. **十分なディスク容量**: 最適化結果の保存に必要な容量を確保
3. **実行時間**: 本番実行は約2分かかります
4. **クリーンアップ**: 自動クリーンアップで古いファイルを削除

## サポート

問題が発生した場合は、以下を確認してください：
1. 仮想環境が正しく有効化されているか
2. 依存関係が正しくインストールされているか
3. データディレクトリが存在するか
4. PowerShellの実行ポリシーが適切に設定されているか 