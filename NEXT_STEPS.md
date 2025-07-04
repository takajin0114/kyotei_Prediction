# 今後のタスク・TODO一覧（kyotei_Prediction）

## 【現状・進捗まとめ】
- A. ディレクトリ・コード整理・README/設計書最新化は完了（2025-07-04時点）
  - data/ ディレクトリの results/・logs/ 新設、sample/統合方針・命名規則統一
  - tools/ 配下は fetch, batch, analysis, viz, ai, common で用途別に整理
  - pipelines/READMEに機能分割・サンプルフロー追記
  - common/READMEに共通処理集約・運用ルール明記
  - fetch/README, integration_design.mdにAPI/CLI/バッチの統一方針を反映
- ルートREADMEを全体のハブとして再構成、各設計書・サブREADME・タスク一覧へのリンクを明記
- integration_design.md, prediction_algorithm_design.md, site_analysis.md, web_app_requirements.md など設計書の冒頭に役割・関連ドキュメント・最終更新日を追加
- サブディレクトリREADMEも役割・使い方・設計書リンクを明記し最新化

---

## A. ディレクトリ・コード整理・リファクタリング（完了）
- [x] データディレクトリのraw/processed/results/logs分割（`data/`の整理）
- [x] `tools/`配下の用途別サブディレクトリ化（fetch, batch, analysis, viz等の明確化）
- [x] `pipelines/`の機能分割・README追加
- [x] 共通処理（会場マッピング・定数・ユーティリティ）の集約
- [x] API/CLI/バッチの引数・出力・エラー処理統一

## B. 機能追加・強化（次作業）
- [ ] **B-1: 3連単確率計算の予測アルゴリズム実装**（prediction_algorithm_design.md・pipelines/に反映）
- [ ] 機材データ重視の予測ロジック強化
- [ ] 選手の調子・競艇場特性・リアルタイムオッズの考慮
- [ ] データベース連携（SQLite等で過去データ蓄積）
- [ ] 統計分析機能の追加
- [ ] 機械学習・ディープラーニングモデルの本格導入
- [ ] 大量データによる重み最適化・相性分析・季節補正など

## C. Webアプリ・UI/UX
- [ ] HTMLテンプレート・JavaScript機能の拡充
- [ ] レスポンシブデザイン対応
- [ ] エラーハンドリング・ユーザー体験向上
- [ ] 予測履歴・分析タブの実装

## D. テスト・運用
- [ ] テスト自動化・カバレッジ向上
- [ ] CI/CD整備
- [ ] ドキュメントの多言語化・自動生成
- [ ] 不要ファイル・大容量ファイルの整理

## E. データ取得・分析
- [ ] metaboatrace.scrapers等の既存ライブラリ活用・検証
- [ ] 独自スクレイピング機能の段階的実装
- [ ] データ取得効率化（並列化・レート制限・欠損検出）

---

### 優先度・推奨アクション（短期）
1. B-1: 3連単確率計算の予測アルゴリズム実装
2. 機材データ重視の予測ロジック強化
3. Webアプリの履歴・分析タブ実装
4. テスト自動化・CI/CD
5. データ取得効率化

---

#### 直近の具体的タスク例
- [ ] **B-1: 3連単確率計算の予測アルゴリズム実装**（prediction_algorithm_design.md・pipelines/に反映）
- [ ] 機材データ重視の予測ロジック強化
- [ ] Webアプリの「履歴」「分析」タブの実装
- [ ] 既存データ取得スクリプトのリファクタ・効率化
- [ ] テスト自動化（pytest等） 