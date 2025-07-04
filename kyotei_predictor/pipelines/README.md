# pipelines ディレクトリ README

**最終更新日: 2025-07-04**

---

## 本READMEの役割
- データ前処理・特徴量生成・AI学習環境などパイプラインの役割・使い方を記載
- 典型的な処理フロー・設計書へのリンクを明記
- ルートREADMEやNEXT_STEPS.mdへのリンクも記載

## 関連ドキュメント
- [../../README.md](../../README.md)（全体概要・セットアップ・タスク入口）
- [../../NEXT_STEPS.md](../../NEXT_STEPS.md)（今後のタスク・優先度・進捗管理）
- [../../integration_design.md](../../integration_design.md)（統合設計・アーキテクチャ）
- [../../prediction_algorithm_design.md](../../prediction_algorithm_design.md)（予測アルゴリズム設計）

---

## 構成・機能分割方針
- 前処理（data_preprocessor.py）・特徴量生成（feature_enhancer.py）・AI学習環境（kyotei_env.py）など、用途別にスクリプトを整理
- 今後は「データ検証」「パイプライン自動化」「追加特徴量」なども用途別に追加
- 共通処理は tools/common/ へ集約

---

## 📁 主なスクリプト
- `data_preprocessor.py` : データ前処理・クリーニング
- `feature_enhancer.py` : 特徴量エンジニアリング
- `kyotei_env.py` : 強化学習用環境クラス

---

## 📝 サンプル処理フロー
```python
# 1. 生データの前処理
from pipelines.data_preprocessor import preprocess_raw_data
cleaned = preprocess_raw_data('data/raw/race_data_20250701_KIRYU_R1.json')

# 2. 特徴量エンジニアリング
from pipelines.feature_enhancer import add_features
featured = add_features(cleaned)

# 3. AI学習環境の構築
from pipelines.kyotei_env import KyoteiEnv
env = KyoteiEnv(featured)
```

---

## 運用方針
- データ取得後、raw/→processed/への変換処理を担当
- AI学習・推論用のデータセット生成
- 新規パイプラインは本ディレクトリに追加
- 共通処理は tools/common/ へ集約

---

## 備考
- 中間生成物は data/processed/ へ保存
- パイプラインの自動化は今後 scripts/ や workflow/ で管理予定
- テストコードは tests/ 配下に設置
- 用途別にスクリプトを整理し、READMEも随時更新 