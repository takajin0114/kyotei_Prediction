# 競艇予測システム ドキュメント

**最終更新日**: 2025-07-06  
**バージョン**: 1.2

---

## 🚩 進行中タスク（2025-07-06時点）

### ✅ 完了済み
- **B-1: 3連単確率計算アルゴリズムのテスト・改善**（Phase 1, 2完了）
  - [TRIFECTA_IMPROVEMENT_PLAN.md](TRIFECTA_IMPROVEMENT_PLAN.md)（詳細計画・結果）
  - [prediction_algorithm_design.md](prediction_algorithm_design.md)（設計方針）
  - **成果**: 実際結果順位を70位台→43位に改善（約40%向上）

- **B-2: 機材データ重視ロジックの強化**（完了）
  - [prediction_algorithm_design.md](prediction_algorithm_design.md)
  - [kyotei_predictor/prediction_engine.py](../kyotei_predictor/prediction_engine.py)
  - **成果**: 実際結果を1位に予測成功（43位→1位、大幅改善）

### 🔄 現在進行中
- **C-1: Webアプリ「履歴」「分析」タブの実装**
  - [web_app_requirements.md](web_app_requirements.md)
  - [integration_design.md](integration_design.md)

### ⏳ 次回予定
- **D: データ取得・バッチ処理のリファクタ・効率化**
  - [site_analysis.md](site_analysis.md)
  - [kyotei_predictor/tools/fetch/](../kyotei_predictor/tools/fetch/)
  - [kyotei_predictor/tools/batch/](../kyotei_predictor/tools/batch/)

### 📋 中長期・運用タスク（今回は未対応）
- **E: 中長期拡張計画**
  - [NEXT_STEPS.md](../NEXT_STEPS.md)参照
- **F: ドキュメント管理・運用**
  - [NEXT_STEPS.md](../NEXT_STEPS.md)参照

---

## 📊 最新の改善結果

### 3連単確率計算アルゴリズム（B-1）
- **最良設定**:
  - 正規化: softmax (temperature=0.1)
  - 重み: 機材重視（boat_quinella_rate: 0.35, motor_quinella_rate: 0.35）
  - 2着重み: 0.8, 3着重み: 0.5
- **性能**: 実際結果順位 43位（改善前: 70位台）
- **課題**: 上位10位以内への到達は未達成

### 機材重視ロジック強化（B-2）
- **強化内容**:
  - 機材相性マトリックスの導入
  - 時系列分析機能の追加
  - 組み合わせ効果の考慮
  - 選手適応性スコアの導入
- **性能**: 実際結果を**1位**に予測成功（43位→1位）
- **予測精度**: 17.50%の確率で的中

### 次のステップ
1. **Webアプリ機能拡張**（C-1）
2. **データ処理効率化**（D）

---

## 📁 ドキュメント構成

### 設計書
- [integration_design.md](integration_design.md) - システム統合設計
- [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測アルゴリズム設計
- [web_app_requirements.md](web_app_requirements.md) - Webアプリ要件定義
- [site_analysis.md](site_analysis.md) - サイト分析・データ取得設計

### 詳細計画・結果
- [TRIFECTA_IMPROVEMENT_PLAN.md](TRIFECTA_IMPROVEMENT_PLAN.md) - 3連単確率計算改善計画・結果
- [EQUIPMENT_ENHANCEMENT_PLAN.md](EQUIPMENT_ENHANCEMENT_PLAN.md) - 機材重視ロジック強化計画・結果

### プロジェクト管理
- [NEXT_STEPS.md](../NEXT_STEPS.md) - 全体の進行計画

---

## 🔧 技術スタック

### バックエンド
- **Python 3.11**
- **Flask** - Webアプリケーション
- **NumPy/Pandas** - データ処理
- **Scikit-learn** - 機械学習（予定）

### フロントエンド
- **HTML/CSS/JavaScript** - Webインターフェース
- **Chart.js** - データ可視化

### データ処理
- **JSON** - データ形式
- **SQLite** - データベース（予定）

---

## 📈 開発状況

### 完了済み機能
- ✅ 基本予測エンジン
- ✅ 3連単確率計算（改善済み）
- ✅ 機材重視アルゴリズム（強化済み）
- ✅ データ取得・処理パイプライン
- ✅ Webアプリ基本機能

### 開発中機能
- 🔄 Webアプリ履歴・分析タブ

### 予定機能
- ⏳ 機械学習モデル導入
- ⏳ 統計的検証システム

---

## 🚀 セットアップ・実行

### 環境構築
```bash
# 仮想環境作成・有効化
python -m venv venv311
venv311\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
$env:PYTHONPATH = "D:\git\kyotei_Prediction"
```

### テスト実行
```bash
# 3連単確率計算テスト
python kyotei_predictor/tests/ai/test_trifecta_probability.py

# パラメータスイープテスト
python kyotei_predictor/tests/ai/test_trifecta_probability.py --sweep

# 強化版機材重視アルゴリズムテスト
python kyotei_predictor/tests/ai/test_equipment_focused_enhanced.py
```

### Webアプリ起動
```bash
python kyotei_predictor/app.py
```

---

## 📞 サポート・連絡

### 開発者
- 競艇予測システム開発チーム

### ドキュメント更新
- 最終更新: 2025-07-06
- 次回更新予定: Webアプリ機能拡張完了後

---

## 🎯 ドキュメントの使い方

### **新規参加者向け**
1. [README.md](../README.md) - プロジェクト概要・セットアップ
2. [integration_design.md](integration_design.md) - システム全体の理解
3. [prediction_algorithm_design.md](prediction_algorithm_design.md) - 予測ロジックの理解

### **開発者向け**
1. [NEXT_STEPS.md](../NEXT_STEPS.md) - 現在のタスク・優先度
2. 各機能別README - 実装詳細
3. [CHANGELOG.md](../CHANGELOG.md) - 最新の変更内容

### **運用者向け**
1. [kyotei_predictor/tools/batch/README.md](../kyotei_predictor/tools/batch/README.md) - バッチ処理運用
2. [PERFORMANCE_IMPROVEMENTS.md](../PERFORMANCE_IMPROVEMENTS.md) - 性能改善履歴
3. [kyotei_predictor/README.md](../kyotei_predictor/README.md) - アプリケーション運用

---

## 📝 ドキュメント更新ルール

### **更新頻度**
- **README.md**: 機能追加・変更時
- **NEXT_STEPS.md**: 週次更新
- **CHANGELOG.md**: リリース時
- **設計書**: 設計変更時

### **更新責任者**
- **プロジェクト全体**: プロジェクトリーダー
- **機能別**: 各機能担当者
- **テスト**: テスト担当者

### **レビュー**
- 重要な変更は必ずレビューを実施
- ドキュメントの整合性を確認
- リンク切れのチェック

---

## 🔗 関連リソース

### **外部リンク**
- [競艇オフィシャルサイト](https://www.boatrace.jp/)
- [競艇データサイト](https://boatrace.jp/owpc/pc/race/)

### **内部リソース**
- [データディレクトリ](../kyotei_predictor/data/)
- [設定ファイル](../kyotei_predictor/config/)
- [テストデータ](../kyotei_predictor/tests/)

---

## 📞 サポート

### **質問・要望**
- GitHub Issues で報告
- ドキュメント改善の提案も歓迎

### **貢献**
- ドキュメントの改善提案
- 翻訳・多言語化
- サンプルコードの追加

---

## 🚀 Phase 4: 投資戦略最適化（詳細タスク）

### 1. 期待値閾値最適化
- 過去データを用いた閾値シミュレーション
- 複数戦略のパフォーマンス比較
- 最適閾値の自動探索

### 2. リアルタイムオッズ取得・更新
- オッズデータのリアルタイム取得・更新機能
- データ取得API/スクレイピング
- オッズ変動への即時対応

### 3. リアルタイム投資判断・自動投資システム
- 投資判断ロジックのリアルタイム化
- 自動投資システムの設計・実装
- 投資実行の安全性・ログ管理

### 4. ポートフォリオ最適化
- 投資組み合わせの最適配分アルゴリズム
- リスク指標の導入
- シミュレーションによる戦略評価

### 5. 要件定義・設計ドキュメント作成
- 各タスクの要件・設計方針まとめ

### 6. 進捗・タスク管理
- README/ドキュメントで進捗管理
- TODOリストの活用

**最終更新**: 2025-07-06  
**次回更新予定**: 2025-07-13 

### 🚀 モデル精度向上タスク（2025-07-08追加）

1. **現状把握・課題の特定**
   - 現行モデルの評価指標・現状精度の整理
   - 誤分類・失敗パターンの分析
2. **データ品質・特徴量の見直し**
   - 学習データの最新化・拡充
   - 欠損・異常値の再チェック
   - 特徴量重要度分析・新規特徴量の追加
3. **モデル構造・ハイパーパラメータの最適化**
   - 現行モデル構造の再確認
   - Optuna等によるハイパーパラメータ最適化
   - アンサンブル・新手法の検討
4. **精度評価・ベンチマーク**
   - バックテスト・A/Bテストの実施
   - KPI（的中率・回収率・シャープレシオ等）の定量評価
5. **運用・継続的改善**
   - 精度検証・改善サイクルの自動化
   - ドキュメント・レポートの随時更新 

#### 📊 現状モデル精度サマリー（2025-07-08時点, 直近1000レース）
- 1着的中数: 47件（4.7%）
- 3着以内的中数: 118件（11.8%）
- 5着以内的中数: 177件（17.7%）
- 10着以内的中数: 299件（29.9%）
- 平均順位: 31.94

（`kyotei_predictor/tools/analysis/trifecta_bulk_validator.py` による自動集計結果） 

#### ❌ 失敗パターン分析（2025-07-08, 直近1000レース）
- 高確率で予測した組み合わせが全て外れるケースが多い
- 1号艇を中心とした予測が多いが、実際は外れるパターンが目立つ
- KIRYU R1など、特定会場・レース番号での外れも散見

例：
- ファイル: race_data_2024-06-06_KIRYU_R1.json
  - 上位予測: 1-2-4 (9.5%), 1-3-4 (8.1%), 1-3-5 (7.3%) いずれも外れ

今後は、これらの失敗傾向を踏まえた特徴量・モデル構造の見直しを進める。 

#### 📝 モデル精度改善の標準フロー（テンプレート）
1. 現状モデルの評価指標・精度を自動集計
2. 失敗パターン・外れ傾向を分析
3. 特徴量・データ品質・モデル構造の見直し案を検討
4. 新規特徴量追加やモデル・ハイパーパラメータの最適化を実施
5. 再学習・再評価を行い、改善効果を検証
6. すべての流れ・結果・気づきをドキュメントに記録

※今後も「データが揃い次第この流れで改善サイクルを回す」ことを推奨 