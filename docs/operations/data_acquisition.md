
# データ取得バッチ運用・実行手順（2024年7月時点）

## 概要
- 競艇レースデータの一括取得・欠損再取得・品質チェックを自動化
- 日付範囲・会場指定・並列数・進捗監視・エラー耐性を強化

## 主な改善点（2024年7月）
- 欠損再取得は「データ取得と同じ日付範囲のみ」対象に限定
- 並列数デフォルト：会場8・レース16
- 多重起動防止・進捗表示・エラー/中止レース自動判定
- テスト運用時は短期間・単会場で検証、本番は全会場・長期間で一括実行

## 実行例

### 基本的なデータ取得（2025年8月時点の推奨方法）

#### 1. 仮想環境のアクティベート
```powershell
# PowerShellで仮想環境をアクティベート
.\venv\Scripts\Activate.ps1

# PYTHONPATHを設定
$env:PYTHONPATH = $PWD
```

#### 2. テスト運用（単一会場・短期間）
```sh
# 桐生競艇場・2日間のテスト
.\venv\Scripts\python.exe -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date 2025-07-01 --end-date 2025-07-02 --stadiums KIRYU
```

#### 3. 本番運用（全会場・1ヶ月分）
```sh
# 2025年7月分の全会場データ取得
.\venv\Scripts\python.exe -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date 2025-07-01 --end-date 2025-07-31 --stadiums ALL
```

### 従来の方法（非推奨）
```sh
# 注意: 以下のコマンドは現在エラーが発生する可能性があります
python -m kyotei_predictor.tools.batch.run_data_maintenance --start-date 2024-03-01 --end-date 2024-04-30 --stadiums ALL
```

## トラブルシューティング（2025年8月時点）

### よくあるエラーと解決方法

#### 1. ImportError: cannot import name 'get_config'
**エラー内容**: `kyotei_predictor.utils.config`から`get_config`関数をインポートできない
**解決方法**: `race_data_fetcher.py`の不要なインポート文を削除済み

#### 2. ImportError: cannot import name 'safe_print'
**エラー内容**: `kyotei_predictor.utils.common`から`safe_print`関数をインポートできない
**解決方法**: `safe_print`は`KyoteiUtils.safe_print`として使用する必要があります

#### 3. NameError: name 'time' is not defined
**エラー内容**: `time.sleep()`で`time`モジュールが未定義
**解決方法**: `odds_fetcher.py`に`import time`を追加済み

#### 4. NameError: name 'StringIO' is not defined
**エラー内容**: `StringIO`が未定義
**解決方法**: `odds_fetcher.py`に`from io import StringIO`を追加済み

### 修正済みファイル
- `kyotei_predictor/tools/fetch/race_data_fetcher.py` - 不要なインポート削除
- `kyotei_predictor/tools/fetch/odds_fetcher.py` - 不足していたインポート追加

### 実行前の確認事項
1. 仮想環境がアクティベートされているか
2. PYTHONPATHが正しく設定されているか
3. 必要な依存関係がインストールされているか
4. 十分なディスク容量があるか（1ヶ月分で約数GB必要）

#### 実行ログ例（2025年7月データ取得の成功例）
```
=== バッチフェッチ完了（完全並列版） ===
対象期間: 2025-07-01 〜 2025-07-31
対象会場: 24会場
総リクエスト数: レース4896件, オッズ4896件
成功数: レース4896件, オッズ4896件
成功率: レース100.0%, オッズ100.0%
失敗数: レース0件, オッズ0件

📊 エラーハンドリング改善:
  - 選手名解析エラー: 自動スキップ処理 + 部分データ保存
  - レース中止: 自動検出・スキップ
  - ネットワークエラー: 最大3回リトライ
  - レート制限: 1秒間隔

バッチ処理終了: 2025-08-11 02:47:05.175416
所要時間: 4:13:31.187601
```

#### 従来の実行ログ例（参考）
```
[CMD] python -u -m kyotei_predictor.tools.batch.batch_fetch_all_venues --start-date 2024-03-01 --end-date 2024-04-30 --stadiums ALL --schedule-workers 8 --race-workers 16 --is-child
バッチ処理開始: 2025-07-11 22:14:10.365549
全24会場バッチフェッチ開始（完全並列版）
期間: 2024-03-01 〜 2024-04-30
対象会場数: 24
レート制限: 1秒
開催日取得並列数: 8
レース取得並列数: 16
=== 全24会場 並列開催日取得開始 ===
並列度: 8
...
```

## 運用指針・注意点（2025年8月時点）
- **推奨**: テスト時は短期間・単会場で動作確認→本番は全会場・長期間で一括実行
- **重要**: 仮想環境のアクティベートとPYTHONPATH設定を必ず実行
- **注意**: 従来の`run_data_maintenance.py`は現在エラーが発生する可能性があります
- **推奨**: `batch_fetch_all_venues.py`を直接使用する方法が安定しています
- 進捗・エラーは標準出力・ログで逐次監視
- 多重起動防止ロジックあり
- 並列数は必要に応じて `--schedule-workers` `--race-workers` で上書き可

## 一連の運用フロー・ノウハウ（2024年7月時点追記）
1. データ取得バッチ（run_data_maintenance.py）で全会場・全期間のデータを一括取得
2. 欠損再取得・品質チェックも同範囲で自動実行
3. 予測ツール（prediction_tool.py）で全日・全会場分の予測をoutputs/predictions_YYYY-MM-DD.jsonとして保存
4. Web表示機能（predictions.html）で最新・過去の予測結果を可視化
5. 進捗・エラー・運用履歴は標準出力・ログ・outputs/scheduled_maintenance_history.jsonで逐次監視
6. バッチ・予測・Web表示の仕様変更時は必ずドキュメントも更新

### 運用履歴・改善点・トラブル事例（2025年8月時点）
- **2025年8月**: データ取得コマンドの大幅な改善と安定化
  - `safe_print`関数のインポート問題を解決
  - `get_config`関数の不要なインポートを削除
  - `time`モジュールと`StringIO`の不足インポートを追加
  - 仮想環境アクティベーション手順を標準化
- **2024年7月**: 欠損再取得が全期間対象になっていた問題を「指定範囲のみ」に修正
- **2024年7月**: 多重起動防止・進捗表示・エラー耐性を強化
- **2024年7月**: 品質チェックで「データ0件」時の0除算エラーを修正
- **2024年7月**: scheduled_data_maintenance.pyで一括自動運用・履歴記録・アラート通知を実装
- **2024年7月**: 予測ツール・Web表示機能の本格運用設計・運用フローをドキュメントに反映

---

## 更新履歴
- **2025年8月11日**: データ取得コマンドの安定化、トラブルシューティング追加
- **2024年7月**: 初版作成、基本的な運用手順を記載

この運用・改善内容は今後も随時アップデート予定です。
