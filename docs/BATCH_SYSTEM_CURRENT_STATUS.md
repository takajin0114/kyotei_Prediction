# バッチシステム 現在の状況

## 概要
競艇予測システムのバッチ処理システムについて、多重起動防止の改善、サブプロセス呼び出しの安全化、およびPowerShellエラーの調査結果を整理したドキュメントです。

## 主要な改善事項

### 1. 多重起動防止のロックファイル方式化

#### 変更前の問題
- Windows環境での `wmic` プロセス判定による多重起動防止
- コマンドライン部分一致による誤検出・漏れの可能性
- クロスプラットフォーム対応の不備

#### 変更後の改善
- **ロックファイル方式**による堅牢な多重起動防止
- 各バッチで固有のロックファイルを作成・管理
- 正常終了・異常終了時の自動ロック解除
- クロスプラットフォーム対応

#### 対象バッチ
- `batch_fetch_all_venues.py` → `batch_fetch_all_venues.lock`
- `run_data_maintenance.py` → `run_data_maintenance.lock`
- `retry_missing_races.py` → `retry_missing_races.lock`
- `fetch_missing_months.py` → `fetch_missing_months.lock`
- `fast_future_entries_fetcher.py` → `fast_future_entries_fetcher.lock`

#### ロックファイルの内容
```json
pid=7248
start=2025-07-15T09:53:03.992039
cmd=python -m kyotei_predictor.tools.batch.run_data_maintenance --start-date 2024-01-04 --end-date 2024-01-04 --stadiums KIRYU
```

### 2. サブプロセス呼び出しの安全化

#### 変更前の問題
- `subprocess.run(cmd, shell=True, ...)` による文字列形式のコマンド実行
- Windows環境での長いコマンドラインや特殊文字による引数パースミス
- エスケープ問題による引数渡しの失敗

#### 変更後の改善
- **リスト形式**による安全なサブプロセス呼び出し
- 引数のパースミスを完全に回避
- クロスプラットフォームでの安定動作

#### 修正例
```python
# 変更前
fetch_cmd = f"python -u -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date {args.start_date}"
subprocess.run(fetch_cmd, shell=True, ...)

# 変更後
fetch_cmd = ["python", "-u", "-m", "kyotei_predictor.tools.batch.batch_fetch_all_venues", "--start-date", args.start_date]
subprocess.run(fetch_cmd, ...)
```

#### 対象ファイル
- `run_data_maintenance.py` の全サブバッチ呼び出し

### 3. 構文エラーの修正

#### 修正内容
- `retry_missing_races.py` の `finally` 節の構文エラーを修正
- `try-finally` ブロックの正しい配置

#### 修正前
```python
def main():
    # ... 処理 ...
    print(f"[INFO] 欠損レース再取得バッチ完了")
    finally:  # ← エラー: tryブロックの外にある
        if not is_child and os.path.exists(lockfile):
            os.remove(lockfile)
```

#### 修正後
```python
def main():
    try:
        # ... 処理 ...
        print(f"[INFO] 欠損レース再取得バッチ完了")
    finally:
        if not is_child and os.path.exists(lockfile):
            os.remove(lockfile)
```

## PowerShellエラーの調査結果

### エラーの詳細
```
System.ArgumentOutOfRangeException: 値には 0 以上で、コンソールの次元のバッファー サイズ未満を指定しなければなりません。
パラメーター名:top
実際の値は 14 です。
```

### 原因
1. **PSReadLine 2.0.0**のバグ
2. **コンソールウィンドウサイズ**が小さい（Height=13）
3. **長いコマンドライン**での表示処理エラー

### 影響範囲
- **バッチ処理**: 影響なし（表示の問題のみ）
- **データ取得**: 正常に動作
- **ロックファイル**: 正常に作成・削除される

### 解決策
1. **PSReadLineの無効化**
   ```powershell
   Remove-Module PSReadLine -Force
   ```

2. **コンソールウィンドウサイズの調整**
   - 手動でPowerShellウィンドウを大きくする
   - 新しいPowerShellウィンドウを開く

3. **コマンドプロンプト（cmd.exe）の使用**

## テスト結果

### 一括バッチ実行テスト（2024-01-04 KIRYU）
1. **データ取得（batch_fetch_all_venues）**: ✅ 成功
   - 全12レースのデータが正常に取得・保存
   - レースデータ（race_data_*.json）とオッズデータ（odds_data_*.json）の両方が作成

2. **取得状況サマリ（list_fetched_data_summary）**: ✅ 成功
   - KIRYU: 2024-01-04 ～ 2024-01-04 (1日分)

3. **欠損データ再取得（retry_missing_races）**: ✅ 成功
   - 欠損レース数: 0（既に全データ取得済み）

4. **データ品質チェック（data_availability_checker）**: ✅ 成功

### ロックファイル動作テスト
- **通常起動**: ロックファイルがなければ正常に起動
- **多重起動防止**: ロックファイルが存在する場合は起動拒否
- **ロック解除**: ロックファイル削除後に再起動可能

## 運用上の注意点

### ロックファイル管理
- 異常終了時は手動でロックファイルを削除
- ロックファイルの内容でプロセス情報を確認可能
- `--is-child` フラグでテスト時はロックチェックをスキップ

### PowerShell使用時
- 長いコマンドラインでのPSReadLineエラーは表示の問題のみ
- バッチ処理自体は正常に動作
- 必要に応じてPSReadLineを無効化

### サブプロセス呼び出し
- リスト形式による安全な引数渡し
- クロスプラットフォーム対応
- エスケープ問題の完全回避

## 今後の改善案

### 1. ロックファイルの自動クリーンアップ
- 一定時間経過後の自動削除機能
- プロセス生存確認機能

### 2. PowerShellエラーの永続的解決
- PowerShellプロファイルでのPSReadLine無効化
- 代替ターミナルの検討

### 3. ログ機能の強化
- ロックファイル操作のログ記録
- サブプロセス実行の詳細ログ

## 関連ドキュメント
- [README.md](../README.md) - プロジェクト概要
- [data_acquisition.md](data_acquisition.md) - データ取得運用
- [integration_design.md](integration_design.md) - システム統合設計

---

**最終更新**: 2025-07-15  
**更新者**: AI Assistant  
**バージョン**: 1.0 