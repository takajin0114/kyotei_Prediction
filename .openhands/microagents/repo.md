# 競艇予測プラットフォーム - 技術ドキュメント v2.0

## 🚩【重要】開発方針アップデート（2025-06-27）

**Phase 0（緊急対応タスク）はスキップし、強化学習（RL）を最優先で推進します。**

- 既存の予測エンジン・データ基盤を活用しつつ、RL環境・特徴量設計・モデル開発・評価を段階的に進めます。
- 従来の「基本機能→強化→最適化」型ロードマップは、RLファースト型に統合。
- フロントエンドやAPIの細かな改善は並行タスクとし、RL開発の進捗を最重視します。

---

## 🎯 今後の主目標

### 投資価値判定型3連単予測の実現
- 各レースの全3連単組み合わせについて、
  1. **AI/強化学習で的中確率を計算**
  2. **公式サイトからリアルタイムで3連単オッズを取得**
  3. **「期待値 = オッズ × 的中確率」で全組み合わせを評価**
  4. **期待値が一定以上の組み合わせのみを投資対象とする**
- これにより「期待値投資」戦略を自動化し、実運用可能な予測システムを目指す

---

## 🏁 RLファースト開発ロードマップ

### 1. 強化学習基盤構築
- [x] 依存関係追加（gymnasium, stable-baselines3, torch, optuna, mlflow等）
- [x] 仮想環境構築・動作確認
- [x] KyoteiEnv（gym.Env）実装（状態・行動・報酬設計）
- [x] サンプルデータで環境テスト
- [x] 複数レース対応（KyoteiEnvManager実装）
- [x] RL学習ループ統合（stable-baselines3/PPOサンプル実装）
- [x] 学習ログ・回収率可視化

### 2. 特徴量エンジニアリング
- [ ] 選手スタート分析・環境要因エンコーディング
- [ ] FeatureEnhancer拡張・RL用特徴量生成
- [ ] 特徴量分布・相関・異常値検証

### 3. 強化学習モデル開発
- [ ] PPO実装（stable-baselines3）
- [ ] カスタムポリシー設計
- [ ] Optunaによるハイパーパラメータ最適化
- [ ] バックテスト・精度評価
- [ ] SACやアンサンブル等の高度化（任意）

### 4. 投資価値判定型3連単予測
- [ ] 3連単全組み合わせの確率計算（AI/強化学習モデル出力）
- [ ] odds_fetcher.py等で3連単オッズを自動取得
- [ ] 期待値計算・投資判定ロジック実装
- [ ] 投資推奨リストの自動生成・可視化

### 5. 統合・評価・運用
- [ ] PredictionEngineへのRL統合
- [ ] API/フロント連携
- [ ] A/Bテスト・CI/CD・モニタリング

### 5. 報酬計算ロジック実装方針
- stepでaction（3連単買い目）を選択→正解着順（race_records）と比較
- 的中時: oddsデータから払戻金（=オッズ×賭け金）を取得、不的中時: 払戻金=0
- reward = 払戻金 - 賭け金（賭け金は固定100円）
- 的中判定はaction→買い目変換後、着順タプルと完全一致かで判定
- oddsデータはbetting_numbersで検索
- 実装後、unittestで的中/不的中パターンのreward計算を検証

### 3. 特徴量ごとの型・前処理方針（案）

| 特徴量                | 型         | 前処理・エンコーディング例                |
|-----------------------|------------|-------------------------------------------|
| pit_number（枠番）    | int        | 1〜6を0〜1にmin-max正規化                 |
| current_rating（級別）| str        | one-hot（A1/A2/B1/B2）                    |
| rate_in_all_stadium   | float      | min-max正規化（例: 0〜10→0〜1）           |
| rate_in_event_going_stadium | float | min-max正規化                             |
| boat_quinella_rate    | float      | min-max正規化                             |
| boat_trio_rate        | float      | min-max正規化                             |
| motor_quinella_rate   | float      | min-max正規化                             |
| motor_trio_rate       | float      | min-max正規化                             |
| stadium（場ID）       | str        | one-hot or ラベルエンコーディング          |
| race_number           | int        | 1〜12を0〜1にmin-max正規化                |
| date                  | str        | 月/曜日/連番などに分解 or 無変換           |
| number_of_laps        | int        | そのまま or min-max正規化                 |
| is_course_fixed       | bool       | 0/1に変換                                 |
| オッズ（3連単120通り）| float      | log(odds+1)変換＋min-max正規化 or クリップ |
| 欠損値                | -          | 0埋め/平均値補完/特殊値/欠損フラグ追加     |

- 各艇ごと特徴量（上記×6）＋レース特徴量＋オッズ120個
- 最終shape例: (6, 選手特徴量数) + レース特徴量数 + 120

### 4. サンプルデータでのベクトル化テスト
- race_data/odds_dataから状態ベクトルを生成する関数を実装
- unittestでshapeや値の正規化・欠損処理も含めて妥当性を確認済み
- 状態ベクトルshape例: (179,)（6艇×特徴量+レース特徴量+オッズ120）

### 6. KyoteiEnvの動作テスト
- reset/stepで的中時は払戻金-賭け金、不的中時は-賭け金のrewardが返ることをunittestで確認済み
- RL環境としての基本動作（状態生成・action受付・損益reward返却）が実装・テスト済み

---

## 🧩 RL学習ループ統合 設計方針（2024-06-27追記）

- KyoteiEnvManagerで複数レースデータを管理し、resetごとにランダムなレースを選択してエピソードを開始。
- stable-baselines3（PPO等）とKyoteiEnvManagerを接続し、RL学習ループを構築。
- 学習ループの基本フロー：
  1. env = KyoteiEnvManager(...)
  2. model = PPO('MlpPolicy', env, ...)
  3. model.learn(total_timesteps=...)
- 学習中はreset→step→reward→doneの流れで複数レースを自動的に切り替え。
- 学習ログ（損益・回収率推移）はTensorBoardやmatplotlib等で可視化予定。

---

## ✅ 進捗表（2024-06-27）
| 項目         | 状況 | 備考 |
|--------------|------|------|
| 環境構築     | ✅   | venv311, 依存OK |
| データ取得   | ✅   | スクレイパー・odds取得OK |
| RL環境雛形   | ✅   | KyoteiEnv雛形・テストOK |
| 複数レース対応 | ✅   | KyoteiEnvManager実装・テストOK |
| RL設計方針   | ✅   | 3連単・損益ベースで決定 |
| 状態設計     | ✅   | 特徴量ベクトル(192次元)実装済み |
| 行動設計     | ✅   | permutations実装済み |
| 報酬設計     | ✅   | odds連携・損益計算実装済み |
| 学習ループ   | ✅   | PPO学習・推論サンプル実装済み |

---

## 🚩 次タスク・優先度（2024-06-27追記）
- [x] stable-baselines3（PPO）によるRL学習ループのサンプル実装
- [x] 学習ログ・回収率の可視化（TensorBoard/matplotlib）
- [x] 学習済みモデルの保存・推論サンプル作成
- [ ] ハイパーパラメータ最適化（Optuna連携）
- [ ] PredictionEngine/フロント連携設計

---

## 🏆 RL設計方針（2024-06-27時点）

- **対象舟券種**：3連単（6艇×5×4=120通り）
- **行動空間**：`gym.spaces.Discrete(120)`、action→買い目はpermutationsでマッピング
- **状態ベクトル**：取得できるjsonデータ（出走表・選手・モーター・レース条件・オッズ等）を最大限活用
- **報酬関数**：損益ベース（的中時: 払戻金-賭け金、不的中時: -賭け金）
- **目的**：回収率最大化（期待値重視）
- **学習データ**：data/配下のrace_data_*.json, odds_data_*.json等
- **仮想環境/依存**：venv311, gymnasium, stable-baselines3, torch, metaboatrace.scrapers等

### 今後の決定・実装事項
- 状態ベクトルの特徴量リスト・前処理方針
- action→買い目変換関数の実装
- 報酬計算ロジック（oddsデータ連携）
- データ抽出・分割・学習ループ設計

---

## 📊 開発状況（2024-06-27 現在）

### 🎉 RL基盤構築完了（2024-06-27）
- ✅ Python 3.11仮想環境（venv311）構築・有効化
- ✅ 主要依存パッケージ（gymnasium, stable-baselines3, torch, optuna, mlflow等）インストール
- ✅ KyoteiEnv（gym.Env）実装・テスト完了
- ✅ KyoteiEnvManager（複数レース対応）実装・テスト完了
- ✅ 状態ベクトル生成（192次元）実装・テスト完了
- ✅ PPO学習ループ実装・動作確認完了
- ✅ 学習済みモデル保存・推論サンプル実装完了
- ✅ TensorBoardログ出力・可視化実装完了

**学習結果サマリー：**
- 10,000 timestepsで学習完了
- 最終エピソード報酬: 14,590円（的中時の高配当）
- 学習中に報酬が-100円から341円まで改善
- 環境・モデル共に正常動作確認済み

| コンポーネント   | 進捗   | バージョン | 担当           |
|------------------|--------|------------|----------------|
| データ取得       | ✅100% | v1.3.0     | データチーム   |
| API基盤          | ✅100% | v1.3.0     | バックエンド   |
| 予測モデル       | 🟢85%  | v1.2.1     | AIチーム       |
| フロントエンド   | 🟡40%  | v1.1.0     | フロントチーム |
| 強化学習         | 🟢60%  | v2.0.0     | AIチーム       |
| 投資価値判定     | 🟡10%  | v2.0.0     | AIチーム       |
| 環境構築         | ✅100% | v2.0.0     | 全体           |

- Python 3.11仮想環境（venv311）構築・有効化済み
- 主要依存パッケージ（Flask, gymnasium, stable-baselines3, torch, optuna, mlflow, metaboatrace.scrapers等）インストール済み
- `pip list`/`import`による動作確認OK
- データ取得・分析スクリプトも正常動作
- 依存競合・ビルドエラーは3.11環境で解消済み

---

## 🛠️ 技術スタック
- **Backend**: Python 3.10, Flask 3.0, FastAPI, PostgreSQL/SQLite, Redis, Pandas, Polars
- **ML**: XGBoost, LightGBM, PyTorch, MLflow, WandB
- **RL**: gymnasium, stable-baselines3, Optuna
- **Frontend**: Vue.js 3, Tailwind CSS, Chart.js, D3.js

---

## 🗃️ データ基盤・特徴量
- DB拡張（RL用テーブル）
- Airflow DAGによる自動更新・DVC連携
- FeatureEnhancerによる特徴量生成
- 選手・機材・環境データの統合
- オッズデータ自動取得

---

## 🤖 強化学習・投資価値判定タスク（詳細）
1. 依存関係・DBスキーマ整備
2. KyoteiEnv（gym環境）実装
3. 特徴量設計・エンジニアリング
4. PPO/SAC等のRLモデル開発
5. バックテスト・A/Bテスト
6. 3連単確率計算・オッズ自動取得・期待値判定
7. PredictionEngine/フロント統合
8. モニタリング・CI/CD

---

## 🔮 将来機能（現開発対象外）
- マルチユーザー/ソーシャル/課金

**注記**: v2.0では開発者単独利用を想定

**リスク管理**:
- データ取得規制変更 → 代替API確保
- 予測精度低下 → フォールバックアルゴリズム準備
- 認証不要設計 → セキュリティ簡素化

**最終更新**: 2025-06-27
**バージョン**: 2.0.0
**ステータス**: 🟢 RLファースト開発中
