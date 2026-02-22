# テストディレクトリ

このディレクトリには、**改善策の手動・バッチテスト**が含まれています。  
**パッケージ内の単体・統合テスト**は `kyotei_predictor/tests/` にあります。

## 📁 テストの二系統

| 場所 | 役割 | 実行方法 |
|------|------|----------|
| **tests/**（このディレクトリ） | 改善策（Phase1–4）の手動検証・学習サイクル確認 | `python quick_test.py` 等（improvement_tests 内） |
| **kyotei_predictor/tests/** | 単体・統合テスト（pytest） | プロジェクトルートで `pytest kyotei_predictor/tests/` |

プロジェクトルートから全テストを実行する例:
```bash
pytest kyotei_predictor/tests/ -v
# 改善策の軽量テストのみ
python tests/improvement_tests/quick_test.py
```

## 📁 ディレクトリ構造（このディレクトリ）

```
tests/
├── README.md                    # このファイル
└── improvement_tests/           # 3連単的中率改善策のテスト
    ├── README.md
    ├── quick_test.py            # 軽量テスト
    ├── simple_learning_verification.py
    ├── minimal_learning_test.py
    └── run_*.bat                # バッチ実行
```

## 🧪 テストの種類

### 1. 改善策テスト (improvement_tests/)

#### quick_test.py
- **目的**: 3連単的中率改善策の基本動作確認
- **内容**: Phase 1-4の各改善策のインポートテストと報酬設計の改善確認
- **実行時間**: 数秒
- **実行方法**:
  ```bash
  cd tests/improvement_tests
  python quick_test.py
  ```

#### simple_learning_verification.py
- **目的**: 改善された報酬設計の実際の学習動作確認
- **内容**: 短時間学習（1000ステップ）と予測機能の動作確認
- **実行時間**: 1-2分
- **実行方法**:
  ```bash
  cd tests/improvement_tests
  python simple_learning_verification.py
  ```

#### minimal_learning_test.py
- **目的**: 最小限の学習テスト
- **内容**: 最適化スクリプトの動作確認
- **実行時間**: 5-10分
- **実行方法**:
  ```bash
  cd tests/improvement_tests
  python minimal_learning_test.py
  ```

#### バッチファイル
- **test_improvements.bat**: 基本的な改善策テスト
- **run_all_tests.bat**: 包括的なテスト実行

### 2. パッケージ内テスト (kyotei_predictor/tests/)

単体・統合テスト（pytest）。Web表示・AI・データ取得・予測ツール等。  
プロジェクトルートで: `pytest kyotei_predictor/tests/`

## 🚀 テスト実行方法

### 軽量テスト（推奨）
```bash
cd tests/improvement_tests
python quick_test.py
```

### 学習検証テスト
```bash
cd tests/improvement_tests
python simple_learning_verification.py
```

### 包括的テスト
```bash
cd tests/improvement_tests
run_all_tests.bat
```

## 📊 期待される結果

### quick_test.py
```
=== 3連単的中率改善策 軽量テスト実行 ===

=== Phase 1: 報酬設計改善テスト ===
的中ケース - 旧報酬: 1080.0, 新報酬: 1350.0, 改善: 270.0
2着的中ケース - 旧報酬: 0, 新報酬: 10, 改善: 10.0
1着的中ケース - 旧報酬: -20, 新報酬: -10, 改善: 10.0
不的中ケース - 旧報酬: -100, 新報酬: -80, 改善: 20.0
Phase 1 テスト完了 ✓

=== 軽量テスト完了 ===
実装された改善策:
- Phase 1: 報酬設計の最適化 ✓
- Phase 2: 学習時間の延長 ✓
- Phase 3: アンサンブル学習の導入 ✓
- Phase 4: 継続的学習の実装 ✓
- 性能監視システム ✓
```

### simple_learning_verification.py
```
=== 簡単な学習検証実行 ===

=== 基本的な学習テスト開始 ===
環境とモデルのインポート成功 ✓
最小限環境を作成中...
最小限モデルを作成中...
モデル作成成功 ✓
短時間学習を実行中... (1000ステップ)
短時間学習完了 ✓
予測テストを実行中...
予測アクション: 4
基本的な学習テスト完了 ✓

=== 改善された報酬関数テスト ===
的中: 報酬 = 1350.0
2着的中: 報酬 = 10
1着的中: 報酬 = -10
不的中: 報酬 = -80
改善された報酬関数テスト完了 ✓

=== 検証結果 ===
基本的な学習テスト: 成功 ✓
改善された報酬関数テスト: 成功 ✓

すべての検証が成功しました！
```

## ⚠️ 注意事項

1. **仮想環境の有効化**: テスト実行前に仮想環境を有効化してください
   ```bash
   .\venv\Scripts\Activate.ps1
   ```

2. **依存関係**: 必要なパッケージがインストールされていることを確認してください
   ```bash
   pip install -r requirements.txt
   ```

3. **実行時間**: 学習検証テストは1-2分かかる場合があります

4. **エラー対処**: エラーが発生した場合は、仮想環境の有効化とパッケージのインストールを確認してください

## 📚 関連ドキュメント

- **改善戦略**: [docs/trifecta_improvement_strategy.md](../docs/trifecta_improvement_strategy.md)
- **実装状況**: [docs/improvement_implementation_summary.md](../docs/improvement_implementation_summary.md)
- **テスト結果**: [docs/test_results_summary.md](../docs/test_results_summary.md)

---

*最終更新: 2025年1月27日* 