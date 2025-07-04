# テストディレクトリ

このディレクトリには、競艇予測システムの各種テストが含まれています。

## 📁 ディレクトリ構造

```
tests/
├── README.md                    # このファイル
├── data/                        # データ関連テスト
│   ├── test_data_fetch.py      # データ取得機能テスト
│   ├── test_multiple_races.py  # 複数レース処理テスト
│   └── simple_race_test.py     # シンプルレーステスト
├── ai/                          # AI/機械学習関連テスト
│   ├── test_kyotei_env.py      # 強化学習環境テスト
│   ├── test_phase2_algorithms.py # Phase2アルゴリズムテスト
│   └── test_trifecta_probability.py # 3連単確率計算テスト
└── viz/                         # 可視化関連テスト（予定）
```

## 🧪 テスト実行方法

### 全テスト実行
```bash
# プロジェクトルートから実行
python -m pytest tests/
```

### カテゴリ別テスト実行

#### データ関連テスト
```bash
python -m pytest tests/data/
```

#### AI/機械学習関連テスト
```bash
python -m pytest tests/ai/
```

### 個別テスト実行

#### データ取得テスト
```bash
python tests/data/test_data_fetch.py
```

#### 複数レース処理テスト
```bash
python tests/data/test_multiple_races.py
```

#### 強化学習環境テスト
```bash
python tests/ai/test_kyotei_env.py
```

#### Phase2アルゴリズムテスト
```bash
python tests/ai/test_phase2_algorithms.py
```

## 📋 テスト内容

### データ関連テスト (`data/`)

#### `test_data_fetch.py`
- レースデータ取得機能のテスト
- エラーハンドリングの検証
- データ形式の妥当性チェック

#### `test_multiple_races.py`
- 複数レースの一括処理テスト
- データ統合機能の検証
- パフォーマンステスト

#### `simple_race_test.py`
- 基本的なレース処理のテスト
- 予測アルゴリズムの動作確認
- エッジケースの検証

### AI/機械学習関連テスト (`ai/`)

#### `test_kyotei_env.py`
- 強化学習環境の動作テスト
- 状態空間とアクション空間の検証
- 報酬関数の動作確認

#### `test_phase2_algorithms.py`
- Phase2予測アルゴリズムのテスト
- 機材重視アルゴリズムの検証
- 3連単確率計算の精度テスト

#### `test_trifecta_probability.py`
- 3連単確率計算機能のテスト
- 確率計算の正確性検証
- エッジケースの処理確認

## 🔧 テスト環境設定

### 必要な依存関係
```bash
pip install pytest
pip install pytest-cov  # カバレッジ測定用
```

### テストデータ
- テスト用のサンプルデータは `data/` ディレクトリに配置
- 必要に応じてテストデータを生成

### 環境変数
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 📊 テスト結果

### カバレッジ測定
```bash
python -m pytest tests/ --cov=kyotei_predictor --cov-report=html
```

### テストレポート生成
```bash
python -m pytest tests/ --html=test_report.html --self-contained-html
```

## 🚨 トラブルシューティング

### インポートエラー
- `PYTHONPATH` が正しく設定されているか確認
- プロジェクトルートからテストを実行

### データファイルが見つからない
- テスト用データファイルが正しい場所に配置されているか確認
- データファイルのパスを相対パスで指定

### 依存関係エラー
- `requirements.txt` の依存関係がインストールされているか確認
- 仮想環境が正しくアクティベートされているか確認

## 📝 テスト追加ガイドライン

### 新しいテストファイルの作成
1. 適切なサブディレクトリに配置
2. ファイル名は `test_*.py` の形式
3. テストクラス名は `Test*` の形式
4. テストメソッド名は `test_*` の形式

### テストケースの記述
```python
import pytest
from pathlib import Path

class TestExample:
    def test_basic_functionality(self):
        """基本的な機能テスト"""
        # テストコード
        assert True
    
    def test_edge_case(self):
        """エッジケースのテスト"""
        # エッジケースのテストコード
        pass
```

### モックの使用
```python
from unittest.mock import patch, MagicMock

def test_with_mock(self):
    with patch('module.function') as mock_func:
        mock_func.return_value = expected_value
        # テストコード
```

## 🔄 CI/CD統合

### GitHub Actions設定例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/
``` 