# ディレクトリ・ドキュメント・ログ整理

**実施日**: 2025-02-12

---

## 1. 実施した変更

### 1.1 バッチの集約（scripts/）

- ルートにあった 5 本の .bat を **`scripts/`** に移動。
- 各バッチの先頭で `cd /d "%~dp0\.."` を実行し、プロジェクトルートに移動してから処理するように変更。
- ルートは README / requirements.txt / optimization_config.ini とディレクトリのみに整理。

| 移動元（ルート） | 移動先 |
|------------------|--------|
| run_optimization_config.bat | scripts/run_optimization_config.bat |
| run_optimization_batch.bat | scripts/run_optimization_batch.bat |
| run_optimization_simple.bat | scripts/run_optimization_simple.bat |
| run_learning_prediction_cycle.bat | scripts/run_learning_prediction_cycle.bat |
| cleanup_old_files.bat | scripts/cleanup_old_files.bat |

### 1.2 ドキュメントの集約（docs/guides/）

- ルートにあった実行系ドキュメントを **`docs/guides/`** に移動・統合。
- ルートの BATCH_USAGE_GUIDE.md, OPTIMIZATION_SCRIPT_GUIDE.md, POWERSHELL_SCRIPT_README.md を削除し、内容を docs/guides/ に集約。

| 移動・統合 | 結果 |
|------------|------|
| BATCH_USAGE_GUIDE.md | docs/guides/batch_usage.md（scripts/ 対応に更新） |
| OPTIMIZATION_SCRIPT_GUIDE.md | docs/guides/optimization_script.md（要約版） |
| POWERSHELL_SCRIPT_README.md | docs/guides/powershell.md（短いメモ） |

### 1.3 ログの整理

- ルートに **`logs/`** を新設し、`.gitkeep` を配置。バッチが書き出す optimization_*.log はここに出力。
- .gitignore に `logs/*.log` を追加。`scripts/*.bat` はリポジトリで管理するため `!scripts/*.bat` で除外解除。

### 1.4 削除したもの

| 対象 | 理由 |
|------|------|
| analysis_results/*.json（3ファイル） | 古い分析結果のため削除 |
| docs/REPOSITORY_ORGANIZATION_GUIDE.md | PROJECT_LAYOUT と役割が重複 |
| docs/WORK_COMPLETION_SUMMARY_20250127.md | 古い作業サマリー |

---

## 2. 整理後のルート構成

```
kyotei_Prediction/
├── README.md
├── requirements.txt
├── optimization_config.ini
├── docs/
├── scripts/        # バッチ一式
├── logs/           # 実行ログ（.gitkeep のみコミット）
├── outputs/
├── kyotei_predictor/
└── tests/
```

---

## 3. 参照

- [PROJECT_LAYOUT.md](PROJECT_LAYOUT.md) - 構成の詳細
- [docs/README.md](README.md) - ドキュメント索引
