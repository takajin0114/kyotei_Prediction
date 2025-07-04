# 競艇予測プラットフォーム - 技術ドキュメント（2024年7月リファクタリング版）

---

## 1. プロジェクト概要

- 競艇（ボートレース）のデータ自動取得・分析・AI予測・Webアプリ化を統合したプラットフォーム
- 強化学習（RL）・Optunaによるハイパーパラメータ最適化・期待値投資戦略の自動化
- 公式サイトからのデータスクレイピング・API・バッチ処理・Web UIまで一気通貫

---

## 2. ディレクトリ構成（推奨リファクタリング案）

```
kyotei_Prediction/
├── kyotei_predictor/           # メインアプリ・データ・API
│   ├── app.py                 # Flask Webアプリ
│   ├── data/                  # 取得データ（raw, processed, results, logs等に分割推奨）
│   ├── tools/                 # データ取得・分析・バッチ・会場マッピング等
│   ├── pipelines/            # 前処理・特徴量・環境生成
│   ├── tests/                # ユニット/統合/シナリオテスト
│   ├── static/               # 静的ファイル
│   ├── templates/            # HTMLテンプレート
│   ├── outputs/              # 可視化・HTML・レポート出力
│   ├── requirements.txt      # 依存関係
│   └── README.md             # サブシステム説明
├── integration_design.md     # 統合設計・アーキテクチャ
├── prediction_algorithm_design.md # 予測アルゴリズム設計
├── site_analysis.md          # サイト・データ分析
├── web_app_requirements.md   # Web要件・UI設計
├── README.md                 # ルート説明（全体像・セットアップ）
└── .openhands/microagents/repo.md # 技術方針・進捗・設計思想（本ファイル）
```

---

## 3. 主要機能・技術スタック

- **データ取得**: 公式サイトスクレイピング（metaboatrace）、バッチ自動化、全24会場対応
- **データ管理**: JSON/CSV/DB化、前処理・特徴量生成
- **AI予測**: 強化学習（PPO, gymnasium, stable-baselines3）、Optuna最適化
- **Webアプリ/API**: Flask, Bootstrap, Chart.js
- **可視化・分析**: HTML, Chart.js, レポート出力
- **CI/CD・テスト**: pytest, unittest, 自動化スクリプト

---

## 4. データ取得・管理

- `tools/batch_fetch_all_venues.py`：全24会場・開催日自動取得＆データ収集
- `tools/venue_mapping.py`：会場コード・名称・地域等の一元管理
- `tools/race_data_fetcher.py`/`odds_fetcher.py`：個別データ取得
- `data/`：raw, processed, results, logs等に細分化推奨

---

## 5. 強化学習（RL）・Optuna最適化

- `pipelines/kyotei_env.py`：RL環境（gym.Env）
- `tools/optuna_optimizer.py`：Optunaによるハイパーパラメータ最適化
- `tools/rl_learn_sample.py`：RL学習サンプル
- `tools/rl_visualization.py`：学習結果可視化
- `optuna_results/`, `optuna_logs/`：最適化ログ・結果

---

## 6. API・Webアプリ


## 9. リファクタリング方針

- **ディレクトリ再編成**：用途別・責務別に整理し、冗長/重複スクリプトを統合・削除
- **README/ドキュメント整理**：ルート/サブディレクトリごとに役割・使い方・API例を明記
- **共通処理の集約**：会場マッピング・定数・ユーティリティは`tools/venue_mapping.py`等に集約
- **テスト・CI/CD強化**：pytest, unittest, 自動化スクリプトの整備
- **API/CLI/バッチの一貫性**：引数・出力・エラー処理・ログの標準化

---

## 10. 参考・設計資料

- `integration_design.md`：統合設計・アーキテクチャ
- `prediction_algorithm_design.md`：予測アルゴリズム設計
- `site_analysis.md`：サイト・データ分析
- `web_app_requirements.md`：Web要件・UI設計

---

**本ドキュメントはリファクタリング・開発方針の最新版です。今後の開発・運用・ドキュメント整理の指針としてください。**
