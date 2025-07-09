# batch ディレクトリ README

**最終更新日: 2025-07-06**

---

## 本READMEの役割
- バッチ処理ツール（大量データ自動収集・スケジュール取得等）の役割・使い方・運用ルールを記載
- 主要スクリプトの説明・設計書へのリンクを明記
- ルートREADMEやtools/README、NEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../../README.md](../../../README.md)（全体概要・セットアップ・タスク入口）
- [../README.md](../README.md)（tools全体の運用ルール）
- [../../../NEXT_STEPS.md](../../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../../integration_design.md](../../../integration_design.md)（統合設計・アーキテクチャ）

---

## 役割・用途
- 全会場・全開催日のデータ一括取得
- スケジュールベースの効率的なデータ収集
- データはdata/raw/に保存

---

## 主要スクリプト
- `batch_fetch_all_venues.py` : 全会場バッチ取得

---

## 運用ルール
- 既存ファイルの重複取得を避ける
- レート制限・エラーハンドリングを徹底
- 不要な一時ファイルは随時削除

---

# 以下、従来の内容（使い方・注意点など）を現状維持・必要に応じて最新化

# Batch Tools

競艇データのバッチ取得ツール群です。大量データの自動収集を担当します。

## 📁 ファイル構成

- `batch_data_fetcher.py` - 基本バッチデータ取得
- `batch_fetch_by_schedule.py` - スケジュールベースバッチ取得
- `batch_fetch_all_venues.py` - 全会場バッチ取得（従来版）
- `batch_fetch_all_venues_parallel.py` - 全会場バッチ取得（並列版・推奨）
- `fast_future_entries_fetcher.py` - 高速未来レース取得

## 🚀 使用方法

### 基本バッチ取得
```bash
python batch_data_fetcher.py
```

### スケジュールベース取得（推奨）
```bash
python batch_fetch_by_schedule.py
```

### 全会場バッチ取得（並列版・推奨）
```bash
# 仮想環境の有効化（必須）
venv311\Scripts\activate

# PYTHONPATH設定とバッチ実行
$env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tools/batch/batch_fetch_all_venues_parallel.py
```

### 全会場バッチ取得（従来版）
```bash
# 仮想環境の有効化（必須）
venv311\Scripts\activate

# PYTHONPATH設定とバッチ実行
$env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tools/batch/batch_fetch_all_venues.py
```

## 📊 取得対象

### 会場
- 全24会場対応（桐生〜大村）
- 地域別・会場別の個別取得可能

### 期間
- 指定期間の全開催日
- 実際のレース開催日のみ取得（効率化）

### データ種別
- レースデータ（出走表・結果等）
- オッズデータ（3連単・3連複等）

## 🔧 技術仕様

### 効率化機能
- **スケジュール事前取得**: 月間スケジュールで開催日を事前特定
- **既存ファイルスキップ**: 重複取得を回避
- **レート制限対応**: 適切な間隔でのリクエスト制御
- **エラーハンドリング**: 例外処理・ログ出力
- **並列処理**: ThreadPoolExecutorによる高速化

### 実行環境設定
- **仮想環境**: venv311の有効化が必須
- **PYTHONPATH**: モジュール解決のため設定が必要
- **実行場所**: プロジェクトルートディレクトリから実行

### 出力形式
- JSON形式で`data/`ディレクトリに保存
- ファイル名規則: `{data_type}_{date}_{venue}_R{race_number}.json`

## 📈 パフォーマンス

### 取得効率
- 開催日のみ取得により無駄なリクエストを削減
- 並列処理による高速化（要実装）

### データ品質
- 整合性チェック機能
- 欠損データの検出・報告 

# バッチデータ取得ツール

## 概要

競艇データの一括取得を行うツール群です。全24会場の過去データを効率的に取得し、機械学習用のデータセットを構築します。

## ツール一覧

### 1. `batch_fetch_all_venues_parallel.py` - 完全並列版バッチフェッチ

**特徴:**
- 全24会場のデータを並列処理で高速取得
- 開催日取得: 8並列
- レースデータ取得: 6並列（1日12レースを6並列）
- 大幅な高速化（従来の80-85%時間短縮）

**エラーハンドリング:**
- ✅ 選手名解析エラー: 自動スキップ処理
- ✅ レース中止: 自動検出・スキップ
- ✅ ネットワークエラー: 最大3回リトライ
- ✅ レート制限: 1秒間隔
- ✅ データ整合性チェック: 不足データの自動補完

**使用方法:**
```bash
# 仮想環境の有効化（必須）
venv311\Scripts\activate

# PYTHONPATH設定とバッチ実行
$env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tools/batch/batch_fetch_all_venues_parallel.py
```

**注意事項:**
- 必ず仮想環境（venv311）を有効化してから実行
- PYTHONPATHの設定が必要（モジュール解決のため）
- プロジェクトルートディレクトリから実行

**性能:**
- 1日分の処理時間: 約1-2分（従来9分から大幅短縮）
- 全24会場30日分: 約12時間（従来60時間から大幅短縮）

### 2. `fast_future_entries_fetcher.py` - 高速未来レース取得

**特徴:**
- 予想用の未来レース出走表のみを高速取得
- レート制限: 0.5秒（通常の半分）
- 並列処理で高速化

**使用方法:**
```bash
# 仮想環境の有効化（必須）
venv311\Scripts\activate

# PYTHONPATH設定とバッチ実行
$env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tools/batch/fast_future_entries_fetcher.py
```

### 3. `batch_fetch_all_venues.py` - 従来版バッチフェッチ

**特徴:**
- シーケンシャル処理
- 安定性重視
- デバッグ用

**使用方法:**
```bash
# 仮想環境の有効化（必須）
venv311\Scripts\activate

# PYTHONPATH設定とバッチ実行
$env:PYTHONPATH = "D:\git\kyotei_Prediction"; python kyotei_predictor/tools/batch/batch_fetch_all_venues.py
```

## エラーハンドリング改善（最新版）

### 選手名解析エラーの対応

**問題:**
```
ValueError: not enough values to unpack (expected 2, got 1)
```

**原因:**
- 選手のフルネームが期待される形式（姓 名）ではなく、単一の名前しかない場合
- 特殊な選手名やデータ形式の違い

**解決策:**
1. **安全なデータ抽出関数**を実装
   - `safe_extract_racers()`: 選手データの安全な抽出
   - `safe_extract_race_entries()`: レース出走データの安全な抽出
   - その他のデータ抽出関数も同様に安全化

2. **データ整合性チェック**
   - 各データの長さを自動調整
   - 不足データは `None` で補完
   - 処理継続を優先

3. **エラー分類と処理**
   - 選手名解析エラー: 即座にスキップ
   - レース中止: 自動検出・スキップ
   - ネットワークエラー: リトライ処理

### 改善されたエラーハンドリング

```python
# 選手名解析エラーの特別処理
except ValueError as e:
    if "not enough values to unpack" in str(e):
        result['race_error'] = f"選手名解析エラー: {e}"
        print(f"    ⚠️  R{race_no}: 選手名解析エラー - スキップ")
        break  # リトライせずにスキップ
```

### データ品質の向上

- **部分的なデータ取得**: 一部のデータが取得できなくても処理継続
- **エラー情報の記録**: どのようなエラーが発生したかを詳細に記録
- **統計情報の改善**: 成功・失敗の詳細な分析

## 設定パラメータ

### 並列処理設定
```python
RATE_LIMIT_SECONDS = 1      # レート制限
MAX_RETRIES = 3             # エラー時のリトライ回数
SCHEDULE_WORKERS = 8        # 開催日取得の並列数
RACE_WORKERS = 6            # レース取得の並列数
```

### 取得期間設定
```python
end_date = date.today()
start_date = end_date - timedelta(days=30)  # 直近30日
```

## 出力ファイル

### レースデータ
```
kyotei_predictor/data/race_data_YYYY-MM-DD_VENUE_RN.json
```

### オッズデータ
```
kyotei_predictor/data/odds_data_YYYY-MM-DD_VENUE_RN.json
```

## 進捗監視

### リアルタイム進捗表示
```
📅 GAMAGORI 2025-07-01 の並列処理開始: 2025-07-06 01:14:30
    R1: ✅race ✅odds
    R2: ✅race ✅odds
    R3: ⚠️ 選手名解析エラー - スキップ
    R4: ✅race ✅odds
  📅 GAMAGORI 2025-07-01 の並列処理終了: 2025-07-06 01:14:50
    結果: レース10/12, オッズ12/12
```

### 統計サマリー
```
=== バッチフェッチ完了（完全並列版） ===
対象期間: 2025-06-06 〜 2025-07-06
対象会場: 24会場
総リクエスト数: レース4320件, オッズ4320件
成功数: レース4104件, オッズ4212件
成功率: レース95.0%, オッズ97.5%
失敗数: レース216件, オッズ108件

📊 エラーハンドリング改善:
  - 選手名解析エラー: 自動スキップ処理
  - レース中止: 自動検出・スキップ
  - ネットワークエラー: 最大3回リトライ
  - レート制限: 1秒間隔
```

## トラブルシューティング

### よくあるエラーと対処法

1. **選手名解析エラー**
   - 自動的にスキップされます
   - データ品質に影響しません

2. **レース中止**
   - 自動検出され、スキップされます
   - 正常な動作です

3. **ネットワークエラー**
   - 最大3回リトライされます
   - それでも失敗した場合はスキップ

4. **レート制限**
   - 1秒間隔で自動調整
   - サーバー負荷を考慮

## 今後の改善予定

- [ ] エラー統計の詳細化
- [ ] 自動リカバリー機能の強化
- [ ] データ品質チェック機能の追加
- [ ] 進捗保存・再開機能の実装 