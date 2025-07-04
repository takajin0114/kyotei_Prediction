# 今後のタスク詳細（2025-07-04時点）

## 1. 直近の優先タスク（B-1, B-2, C-1）

### B-1: 3連単確率計算アルゴリズムの本実装
- [ ] `pipelines/`配下に`trifecta_probability.py`（仮）を新設し、120通りの3連単組み合わせ確率計算をクラス化
- [ ] `prediction_algorithm_design.md`の設計方針に沿い、選手・機材・オッズ・コース特性を重み付け
- [ ] テスト用サンプルデータ（`data/sample/`）で自動テスト（`tests/ai/`）を作成
- [ ] 実装例・利用例を`pipelines/README.md`に追記

### B-2: 機材データ重視ロジックの強化
- [ ] `prediction_engine.py`の`_equipment_focused_algorithm`をリファクタし、ボート・モーター成績の閾値・ボーナス加算ロジックを明示化
- [ ] テストケース追加（高性能機材・低性能機材の極端例も含む）
- [ ] サンプルデータでの特徴分析・可視化（`tools/analysis/`）

### C-1: Webアプリ「履歴」「分析」タブの実装
- [ ] `templates/index.html`に新タブ追加（履歴・分析）
- [ ] Flaskルーティング・API（`/api/predictions_history`, `/api/analysis`等）を`app.py`に追加
- [ ] 履歴データはDBまたは`predictions.json`から取得
- [ ] 分析タブは`tools/analysis/race_stats.py`の可視化APIを呼び出し

---

## 2. データベース・統計分析の拡張

### DBスキーマ・API拡張
- [ ] `pipelines/db_integration.py`に「予測結果」「学習ログ」「特徴量」テーブル追加
- [ ] Webアプリからの履歴検索・分析APIを拡張
- [ ] DBスキーマ・運用ルールを`integration_design.md`・`pipelines/README.md`に反映

### 統計分析・可視化
- [ ] `tools/analysis/race_stats.py`に「コース別・選手別・機材別」集計APIを追加
- [ ] 欠損値・異常値の自動検出・レポート生成
- [ ] matplotlib/plotlyによるグラフ出力例を`README.md`に追記

---

## 3. テスト・CI/CD・運用

- [ ] pytestによる自動テストカバレッジ向上（`tests/`配下を拡充）
- [ ] GitHub Actions等によるCI/CDパイプライン整備
- [ ] ドキュメント自動生成（Sphinx/Markdown）・多言語化
- [ ] 不要ファイル・大容量ファイルの整理・.gitignoreの見直し

---

## 4. データ取得・バッチ処理

- [ ] `tools/fetch/`・`tools/batch/`の既存スクリプトをリファクタ
- [ ] metaboatrace.scrapers等の外部ライブラリ検証・導入
- [ ] 独自スクレイピング機能の段階的実装（HTML構造解析・レート制限・エラー処理）
- [ ] 並列化・効率化（multiprocessing/threading/asyncio等）

---

## 5. 中長期拡張・研究開発

- [ ] 機械学習・ディープラーニングモデルの本格導入（特徴量設計・重み最適化・Optuna活用）
- [ ] 選手間の相性・季節補正・コース適性の高度分析
- [ ] WebアプリUI/UX強化（レスポンシブ・アクセシビリティ・エラーハンドリング）
- [ ] 予測精度の自動評価・改善サイクルの構築

---

## 6. ドキュメント・進捗管理

- [ ] 各設計書（`integration_design.md`, `prediction_algorithm_design.md`, `site_analysis.md`, `web_app_requirements.md`）の最新化
- [ ] サブディレクトリREADMEの運用例・API例・設計方針の追記
- [ ] 本`NEXT_STEPS.md`の定期更新・進捗チェック

---

### ※ 各タスクの詳細・進捗・優先度は本ファイルおよび`README.md`・設計書に随時反映してください。 