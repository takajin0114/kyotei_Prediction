# 競艇予測ツール - リポジトリ情報

## プロジェクト概要
競艇（ボートレース）の予測を支援するWebアプリケーション

## リポジトリ構成

### メインディレクトリ
```
/workspace/
├── .openhands/
│   └── microagents/
│       └── repo.md              # このファイル
├── kyotei_predictor/            # メインアプリケーション
│   ├── app.py                   # Flask Webアプリケーション
│   ├── requirements.txt         # Python依存関係
│   ├── predictions.json         # 予想履歴データ（実行時生成）
│   ├── templates/
│   │   └── index.html          # HTMLテンプレート
│   └── static/
│       ├── css/
│       │   └── style.css       # カスタムスタイル
│       └── js/
│           └── app.js          # JavaScript機能
├── README.md                    # プロジェクト説明書
└── .gitignore                   # Git除外設定
```

## 技術スタック

### Backend
- **Python 3.8+**
- **Flask 3.1.1** - Webフレームワーク
- **pandas** - データ処理
- **numpy** - 数値計算

### Frontend
- **HTML5** - マークアップ
- **CSS3** - スタイリング
- **JavaScript (ES6+)** - インタラクティブ機能
- **Bootstrap 5** - UIフレームワーク
- **Chart.js** - グラフ表示
- **Font Awesome** - アイコン

## 主要機能

### 1. 選手データ分析
- 勝率、連対率、平均スタートタイムの表示
- 選手選択機能
- データの視覚化

### 2. レース条件表示
- 天候情報（晴れ、曇り、雨など）
- 風速・風向データ
- 水温・波高情報

### 3. 予測アルゴリズム
- 複数要素を考慮した総合スコア計算
- 勝率 (40%), 連対率 (30%), スタートタイム (30%) の重み付け
- 天候・風速による補正

### 4. 予想管理
- 予測結果の保存機能
- メモ付き履歴管理
- JSON形式でのデータ永続化

### 5. 統計分析
- Chart.jsによるグラフ表示
- 勝率の棒グラフ
- スタートタイムの折れ線グラフ

### 6. UI/UX
- レスポンシブデザイン
- タブ切り替えインターフェース
- リアルタイム更新

## API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/` | GET | メインページ |
| `/api/racers` | GET | 選手データ取得 |
| `/api/race_conditions` | GET | レース条件取得 |
| `/api/predict` | POST | 予測実行 |
| `/api/save_prediction` | POST | 予想保存 |
| `/api/predictions_history` | GET | 予想履歴取得 |

## セットアップ手順

### 1. 環境準備
```bash
# Python 3.8+ が必要
python --version
```

### 2. 依存関係インストール
```bash
cd kyotei_predictor
pip install -r requirements.txt
```

### 3. アプリケーション起動
```bash
python app.py
```

### 4. アクセス
ブラウザで `http://localhost:12000` にアクセス

## 開発情報

### Git情報
- **リポジトリ**: `takajin0114/kyotei_Prediction`
- **メインブランチ**: `main`
- **開発ブランチ**: `feature/kyotei-web-app`
- **プルリクエスト**: [#1](https://github.com/takajin0114/kyotei_Prediction/pull/1)

### 開発環境
- **開発者**: openhands
- **開発日**: 2025-06-13
- **使用AI**: Claude 3.5 Sonnet

## 今後の拡張計画

### Phase 1: データ連携

#### 1. 技術基盤の構築
- [x] **スクレイピング環境の構築** ✅ 完了
  - `metaboatrace.scrapers==3.3.1` ライブラリ導入
  - 高品質・テスト済みスクレイピング機能
  - レート制限とエラーハンドリング内蔵
  - **成果物**: `test_data_fetch.py`, `race_data_20240615_KIRYU_R1.json`

- [ ] **データベース設計・構築**
  - SQLite → PostgreSQL移行を想定した設計
  - テーブル設計：
    - `racers` (選手マスタ)
    - `races` (レース情報)
    - `race_results` (レース結果)
    - `venues` (競艇場マスタ)
  - インデックス設計とパフォーマンス最適化

#### 2. データ取得の実装
- [x] **競艇公式サイト調査・分析** ✅ 完了
  - ボートレース公式サイト (https://www.boatrace.jp/) の構造分析
  - 既存ライブラリ `metaboatrace.scrapers` の発見・調査
  - robots.txt確認と利用規約遵守の方針策定
  - データ取得可能な範囲の特定完了
  - アクセス頻度制限の設定 (5秒間隔推奨)
  - **レース前情報 + レース結果の完全取得確認済み**
  - **詳細**: `/workspace/site_analysis.md` 参照

- [ ] **選手データ取得機能**
  - 選手登録番号、氏名、所属支部
  - 級別、出身地、生年月日
  - 通算成績（勝率、連対率、3連対率）
  - 最近の成績動向

- [ ] **レース情報取得機能**
  - 開催場、開催日、レース番号
  - 出走表（選手、モーター、ボート情報）
  - レース条件（距離、天候、風速、水温）
  - 締切時刻、発走時刻

- [ ] **レース結果取得機能**
  - 着順、決まり手、タイム
  - スタートタイミング
  - オッズ情報（3連単、3連複、2連単等）
  - 払戻金情報

#### 3. データ処理・管理
- [ ] **データクレンジング機能**
  - 重複データの除去
  - データ形式の統一化
  - 欠損値の処理
  - データ品質チェック

- [ ] **データ更新機能**
  - 定期的なデータ取得スケジューラー
  - 差分更新機能
  - データ整合性チェック
  - バックアップ機能

#### 4. 法的・倫理的対応
- [ ] **コンプライアンス対応**
  - robots.txt遵守の確認
  - アクセス頻度の適切な制限
  - 利用規約の確認と遵守
  - 著作権・肖像権への配慮

- [ ] **エラーハンドリング**
  - ネットワークエラー対応
  - サイト構造変更への対応
  - ログ機能の実装
  - 異常検知とアラート

#### 5. 実装スケジュール (更新版)
```
Week 1: 環境構築・サイト調査 ✅ 完了
├── ✅ 競艇公式サイトの構造分析 (完了)
├── ✅ 既存ライブラリ調査 (metaboatrace.scrapers発見)
├── ✅ 実装方針決定 (Option 1: 既存ライブラリ活用)
└── ✅ スクレイピング環境のセットアップ (完了)

Week 2: データ取得機能実装 ✅ 完了
├── ✅ 既存ライブラリの動作確認・検証 (完了)
├── ✅ レース前情報取得機能の実装 (出走表)
├── ✅ レース結果取得機能の実装
├── ✅ データ表形式表示機能の実装
└── ✅ 基本的なエラーハンドリング (ライブラリ内蔵)

Week 3: データベース設計・連携 🔄 開始
├── ⏳ データベース設計・スキーマ定義
├── ⏳ データベース連携機能の実装
├── ⏳ データ永続化・検索機能
└── ⏳ 過去データ蓄積・分析基盤

Week 4: 最適化・テスト
├── パフォーマンス最適化
├── 統合テスト
└── 既存アプリとの連携
```

## 📊 取得データの完全整理

### 🏁 **実装完了: 2024年6月15日 桐生競艇場 第1レース** データ取得・表示

#### 📋 **レース基本情報**
- **日付**: 2024年6月15日
- **競艇場**: 桐生競艇場 (KIRYU)
- **レース番号**: 第1レース
- **タイトル**: 予選
- **締切時刻**: 06:20:00
- **周回数**: 3周

#### 🚤 **出走表データ（レース前情報）**

| 艇番 | 選手名 | 登録番号 | 級別 | 全国勝率 | 当地勝率 | ボート番号 | ボート2連率 | モーター番号 | モーター2連率 |
|------|--------|----------|------|----------|----------|------------|-------------|--------------|---------------|
| 1 | 渡辺 史之 | 4078 | **B1** | 3.89 | 4.36 | 42 | 34.2% | 75 | 29.5% |
| 2 | 横井 健太 | 3776 | **B1** | 3.95 | 3.00 | 32 | 44.6% | 19 | 38.3% |
| 3 | 松尾 基成 | 3741 | **B1** | 4.07 | 4.22 | 45 | 36.1% | 54 | 40.0% |
| 4 | 齋藤 達希 | 4740 | **B1** | 4.68 | 3.31 | 30 | 36.8% | 17 | 39.5% |
| 5 | 北川 太一 | 4718 | **A2** | **5.75** ⭐ | **7.11** ⭐ | 54 | 29.8% | 27 | 32.2% |
| 6 | 上之 晃弘 | 3843 | **A2** | 4.89 | 5.20 | 70 | 23.9% | 13 | 28.1% |

**📈 出走表分析:**
- **A級選手**: 2名（5号艇・6号艇）
- **最高勝率**: 5号艇 北川太一 (A2級) 全国勝率5.75
- **当地最高勝率**: 5号艇 北川太一 当地勝率7.11

#### 🏁 **レース結果データ**

| 着順 | 艇番 | 選手名 | スタートコース | スタートタイム | 総タイム | 決まり手 |
|------|------|--------|----------------|----------------|----------|----------|
| **1着** 🏆 | **3** | **松尾 基成** | 3 | 0.19秒 | 112.0秒 | **MAKURI** |
| 2着 | 5 | 北川 太一 | 5 | **0.12秒** ⚡ | 112.9秒 | - |
| 3着 | 6 | 上之 晃弘 | 6 | 0.18秒 | 114.1秒 | - |
| 4着 | 1 | 渡辺 史之 | 1 | 0.17秒 | 114.8秒 | - |
| 5着 | 2 | 横井 健太 | 2 | 0.22秒 | 115.2秒 | - |
| 6着 | 4 | 齋藤 達希 | 4 | 0.16秒 | 118.1秒 | - |

**🎯 レース結果分析:**
- **1着**: 3号艇 松尾基成（B1級・勝率4.07）が「まくり」で勝利
- **最速スタート**: 5号艇 北川太一（0.12秒）→ 2着
- **最高勝率選手**: 5号艇 北川太一（A2級・勝率5.75）→ 2着

#### 🌤️ **天候・コンディション**

| 天候 | 風速 | 風向 | 気温 | 水温 | 波高 |
|------|------|------|------|------|------|
| 晴れ (FINE) | 4.0m/s | 202.5度 | 28.0℃ | 24.0℃ | 3.0cm |

#### 💰 **払戻情報**

| 賭式 | 買い目 | 払戻金 |
|------|--------|--------|
| **3連単** | **3-5-6** | **14,690円** |

**💡 配当分析:**
- **中穴配当**: 14,690円（約147倍）
- **人気薄の1着**: B1級の3号艇が1着で高配当
- **A級選手**: 5号艇・6号艇が2着・3着で絡む

#### 🔍 **予想vs結果の検証**

**予想のポイント:**
1. **本命**: 5号艇 北川太一（A2級・最高勝率5.75）
2. **対抗**: 6号艇 上之晃弘（A2級・勝率4.89）
3. **穴**: 4号艇 齋藤達希（B1級だが勝率4.68）

**実際の結果:**
1. **1着**: 3号艇 松尾基成（B1級・勝率4.07）← **大穴**
2. **2着**: 5号艇 北川太一（本命選手）
3. **3着**: 6号艇 上之晃弘（対抗選手）

**勝因分析:**
- **3号艇の勝因**: スタートタイム0.19秒から3コース「まくり」で差し切り、当地勝率4.22で地元適性あり
- **5号艇が2着の理由**: 最速スタート0.12秒で好位置確保も、3号艇の「まくり」に屈する

#### 📈 **取得可能データの種類**

**✅ 実装済み:**
1. **📋 レース基本情報**: 日付、競艇場、タイトル、締切時刻
2. **🚤 出走表**: 選手情報、勝率、ボート・モーター成績
3. **🏁 レース結果**: 着順、タイム、決まり手
4. **🌤️ 天候情報**: 天気、風速、気温、水温
5. **💰 払戻情報**: 各賭式の配当金

**📊 表示形式:**
1. **コンソール表形式**: pandas DataFrame
2. **HTML表形式**: スタイル付きテーブル（A級/B級色分け、1着ハイライト）
3. **JSON形式**: 構造化データ

#### 🎯 **データの活用可能性**

**予測に使えるデータ:**
- **選手成績**: 全国勝率、当地勝率
- **機材成績**: ボート・モーター2連率
- **天候条件**: 風速、風向、気温
- **コース条件**: スタートコース、周回数

**検証に使えるデータ:**
- **実際の着順**: 予想精度の測定
- **スタートタイム**: スタート技術の評価
- **決まり手**: 戦法の分析
- **配当金**: 的中時の収益計算

#### 🛠️ **実装ファイル一覧**

**データ取得:**
- `race_data_fetcher.py`: 完全なレースデータ取得ツール
- `test_data_fetch.py`: 初期データ取得テストスクリプト

**データ表示:**
- `data_display.py`: コンソール表形式表示ツール
- `html_display.py`: HTML表形式表示ツール

**データファイル:**
- `complete_race_data_20240615_KIRYU_R1.json`: 完全レースデータサンプル
- `entry_only_20240615_KIRYU_R1.json`: 出走表のみデータサンプル
- `complete_race_data_20240615_KIRYU_R1.html`: HTML表示サンプル

**使用方法:**
```bash
# データ取得
cd /workspace/kyotei_predictor
python race_data_fetcher.py

# 表形式表示
python data_display.py complete_race_data_20240615_KIRYU_R1.json

# HTML表示生成
python html_display.py complete_race_data_20240615_KIRYU_R1.json
```

## 🗄️ Phase 1 Week 3: データベース設計・連携

### 📋 **実装計画**

#### 1. **データベース設計・スキーマ定義**

**🎯 目標**: 取得した競艇データを効率的に保存・検索できるデータベース設計

**📊 対象データ分析**:
現在取得可能な5カテゴリのデータを正規化してテーブル設計

**🏗️ 設計方針**:
- **正規化**: データの重複を避け、整合性を保つ
- **パフォーマンス**: 予測・分析に必要なクエリを高速化
- **拡張性**: 将来的なデータ追加に対応
- **SQLite**: 軽量で導入が容易、後にPostgreSQLへ移行可能

#### 2. **テーブル設計**

**🏟️ stadiums（競艇場マスタ）**
```sql
CREATE TABLE stadiums (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,  -- 'KIRYU', 'TODA' など
    name TEXT NOT NULL,         -- '桐生競艇場', '戸田競艇場'
    prefecture TEXT,            -- '群馬県', '埼玉県'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**🏁 races（レース基本情報）**
```sql
CREATE TABLE races (
    id INTEGER PRIMARY KEY,
    stadium_id INTEGER NOT NULL,
    race_date DATE NOT NULL,
    race_number INTEGER NOT NULL,
    title TEXT,                 -- '予選', '一般戦'
    deadline_at TIMESTAMP,      -- 締切時刻
    number_of_laps INTEGER,     -- 周回数
    is_course_fixed BOOLEAN,    -- コース固定
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stadium_id) REFERENCES stadiums(id),
    UNIQUE(stadium_id, race_date, race_number)
);
```

**👤 racers（選手マスタ）**
```sql
CREATE TABLE racers (
    id INTEGER PRIMARY KEY,
    registration_number INTEGER UNIQUE NOT NULL,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    branch TEXT,                -- 支部
    born_prefecture TEXT,       -- 出身地
    birth_date DATE,           -- 生年月日
    height INTEGER,            -- 身長(cm)
    gender TEXT,               -- 性別
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**🚤 race_entries（出走表）**
```sql
CREATE TABLE race_entries (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    pit_number INTEGER NOT NULL,    -- 艇番
    racer_id INTEGER NOT NULL,
    current_rating TEXT,            -- 級別 (A1, A2, B1, B2)
    rate_in_all_stadium REAL,       -- 全国勝率
    rate_in_event_going_stadium REAL, -- 当地勝率
    boat_number INTEGER,            -- ボート番号
    boat_quinella_rate REAL,        -- ボート2連率
    boat_trio_rate REAL,            -- ボート3連率
    motor_number INTEGER,           -- モーター番号
    motor_quinella_rate REAL,       -- モーター2連率
    motor_trio_rate REAL,           -- モーター3連率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (racer_id) REFERENCES racers(id),
    UNIQUE(race_id, pit_number)
);
```

**🏆 race_results（レース結果）**
```sql
CREATE TABLE race_results (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    pit_number INTEGER NOT NULL,
    start_course INTEGER,           -- スタートコース
    start_time REAL,               -- スタートタイム
    total_time REAL,               -- 総タイム
    arrival INTEGER,               -- 着順
    winning_trick TEXT,            -- 決まり手
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE(race_id, pit_number)
);
```

**🌤️ weather_conditions（天候情報）**
```sql
CREATE TABLE weather_conditions (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    weather TEXT,                  -- 天候
    wind_velocity REAL,            -- 風速
    wind_angle REAL,               -- 風向
    air_temperature REAL,          -- 気温
    water_temperature REAL,        -- 水温
    wavelength REAL,               -- 波高
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE(race_id)
);
```

**💰 payoffs（払戻情報）**
```sql
CREATE TABLE payoffs (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    betting_method TEXT NOT NULL,   -- 'TRIFECTA', 'TRIO', 'EXACTA'
    betting_numbers TEXT NOT NULL,  -- '3-5-6' (JSON配列も可)
    amount INTEGER NOT NULL,        -- 払戻金額
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(id)
);
```

#### 3. **インデックス設計**

**🚀 パフォーマンス最適化のためのインデックス**:
```sql
-- レース検索用
CREATE INDEX idx_races_date_stadium ON races(race_date, stadium_id);
CREATE INDEX idx_races_date ON races(race_date);

-- 選手検索用
CREATE INDEX idx_racers_registration ON racers(registration_number);
CREATE INDEX idx_racers_name ON racers(last_name, first_name);

-- 出走表検索用
CREATE INDEX idx_entries_race_pit ON race_entries(race_id, pit_number);
CREATE INDEX idx_entries_racer ON race_entries(racer_id);

-- 結果検索用
CREATE INDEX idx_results_race ON race_results(race_id);
CREATE INDEX idx_results_arrival ON race_results(arrival);

-- 払戻検索用
CREATE INDEX idx_payoffs_race_method ON payoffs(race_id, betting_method);
```

#### 4. **データベース連携機能の実装**

**🔧 実装予定機能**:

**4-1. データベース接続・初期化**
- SQLiteデータベースファイルの作成
- テーブル作成・マイグレーション機能
- 接続プール管理

**4-2. データ挿入機能**
- JSONデータからデータベースへの一括挿入
- 重複データのチェック・更新
- トランザクション管理

**4-3. データ検索機能**
- 日付・競艇場での絞り込み検索
- 選手別成績検索
- レース結果検索
- 統計情報取得

**4-4. データ更新・削除機能**
- 選手情報の更新
- レースデータの修正
- 古いデータの削除

#### 5. **実装ファイル構成**

```
kyotei_predictor/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemyモデル定義
│   ├── connection.py      # データベース接続管理
│   ├── migrations/        # マイグレーションファイル
│   │   └── 001_initial.sql
│   └── queries.py         # よく使うクエリ集
├── data_manager.py        # データ挿入・更新の統合管理
├── db_setup.py           # データベース初期化スクリプト
└── db_test.py            # データベース機能テスト
```

#### 6. **実装スケジュール**

**Day 1-2: データベース設計・セットアップ**
- スキーマ定義・テーブル作成
- SQLAlchemyモデル実装
- 初期化スクリプト作成

**Day 3-4: データ挿入機能**
- JSONからデータベースへの変換
- 一括挿入機能
- 重複チェック機能

**Day 5-6: データ検索機能**
- 基本的なCRUD操作
- 複雑な検索クエリ
- 統計情報取得

**Day 7: テスト・最適化**
- 機能テスト
- パフォーマンステスト
- ドキュメント作成

#### 7. **期待される成果**

**✅ 完了予定機能**:
- 📊 **構造化データ保存**: 正規化されたテーブルでの効率的なデータ管理
- 🔍 **高速検索**: インデックスによる高速なデータ検索
- 📈 **統計分析基盤**: 過去データを活用した分析機能
- 🔄 **データ更新**: リアルタイムでのデータ更新・同期
- 📋 **データ整合性**: 外部キー制約による整合性保証

**🎯 活用例**:
- 選手の過去成績分析
- 競艇場別の傾向分析
- 天候条件と結果の相関分析
- 予測モデルの学習データ準備

#### 8. **技術スタック**

- **データベース**: SQLite → PostgreSQL（将来）
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic
- **接続管理**: SQLAlchemy Engine Pool
- **テスト**: pytest + SQLite in-memory

#### 5-A. 実装方針の選択肢
**Option 1: 既存ライブラリ活用** (推奨 ★★★★★)
- `metaboatrace.scrapers` を使用
- 迅速な実装、高品質保証

**Option 2: 独自実装** (★★☆☆☆)
- 完全カスタマイズ可能
- 開発工数大、リスク高

**Option 3: ハイブリッド** (★★★★☆)
- 既存ライブラリ + 必要部分のカスタマイズ

#### 6. 成果物
- [ ] **スクレイピングモジュール** (`kyotei_predictor/scraper/`)
- [ ] **データベースモデル** (`kyotei_predictor/models/`)
- [ ] **データ取得スケジューラー** (`kyotei_predictor/scheduler/`)
- [ ] **データ品質管理ツール** (`kyotei_predictor/utils/`)
- [ ] **設定ファイル** (`config.yaml`)
- [ ] **ドキュメント** (API仕様書、運用手順書)

- [ ] ~~リアルタイムオッズ情報~~ (Phase 2以降に延期)

### Phase 2: 機械学習
- [ ] より高度な予測モデル
- [ ] 過去データからの学習
- [ ] 予測精度の向上

### Phase 3: ユーザー機能
- [ ] ユーザー認証システム
- [ ] 個人の予想成績管理
- [ ] ソーシャル機能

### Phase 4: 分析強化
- [ ] コース別成績分析
- [ ] 天候別パフォーマンス
- [ ] より詳細な統計情報

## 注意事項

### セキュリティ
- 現在は開発環境用の設定
- 本番環境では適切なセキュリティ設定が必要
- データベース接続の暗号化推奨

### パフォーマンス
- 大量データ処理時の最適化が必要
- キャッシュ機能の実装を検討
- データベース使用への移行を推奨

### 法的考慮
- ギャンブル関連の法規制遵守
- データ利用規約の確認
- 責任あるギャンブルの推進

## サポート・連絡先

### 技術的な質問
- GitHub Issues を利用
- プルリクエストでの改善提案歓迎

### ライセンス
MIT License - 詳細は LICENSE ファイルを参照

---

**最終更新**: 2025-06-13  
**バージョン**: 1.0.0  
**ステータス**: 開発完了・プルリクエスト作成済み