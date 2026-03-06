# アーキテクチャ層分離（Layered Architecture）

責務の境界を明確にした構成の説明。A→B 移行・OS 非依存化の基盤の上に、domain / application / infrastructure / cli を導入している。

---

## 1. 現状構造

```
kyotei_predictor/
  domain/           # 純粋な業務ロジック（データ構造・メトリクス計算）
  application/      # ユースケース（検証・予測・最適化・一連実行）
  infrastructure/   # I/O（config 読込、ファイル保存、パス解決）
  cli/              # 実行入口（python -m kyotei_predictor.cli.*）
  tools/            # 互換レイヤー（既存スクリプト・CLI から呼ばれる。内部は application に委譲）
  config/           # 設定管理（improvement_config 等）
  utils/            # 共通ユーティリティ（betting_selector 等）
  ...
```

- **scripts/** は従来どおり .bat / .ps1 / .sh で、venv 有効化と `python -m kyotei_predictor.cli.*` または tools の起動のみ担当。
- **config** 運用（optimization_config.ini, improvement_config.json）は維持。

---

## 2. domain / application / infrastructure / cli の役割

| 層 | 役割 | 含めるもの | 含めないもの |
|----|------|------------|--------------|
| **domain** | 純粋な業務ロジック | 評価メトリクス（ROI・的中率）、検証のデータ構造（VerificationSummary, VerificationDetail）、ベッティングのデータ構造（PredictionCandidate, SelectedBet）、本質的な計算（get_actual_trifecta, get_odds_for_combination, aggregate_verification_to_summary） | I/O、CLI、フレームワーク依存 |
| **application** | ユースケース | 検証・予測・最適化・学習→予測→検証の一連実行（verify_usecase, predict_usecase, optimize_usecase, run_cycle_usecase） | 直接のファイルパス解決・CLI 引数パース |
| **infrastructure** | I/O・環境依存 | config 読込（config_loader）、JSON 読込・保存（file_loader, result_repository）、パス解決（path_manager） | 業務ルール、ユースケースの制御 |
| **cli** | 実行入口 | 引数パース、config 読込、application usecase の呼び出し（現状は tools 経由で間接呼び出し） | ビジネスロジック、ファイル I/O の詳細 |

---

## 3. tools の互換レイヤー

- **tools** は削除せず、既存の import と scripts からの呼び出しを維持する。
- 実装は **application 層に委譲** し、tools は薄いラッパーとする。

例（検証）:

- `tools.verify_predictions.run_verification` → `application.verify_usecase.run_verify` を呼び、同じ `(summary_dict, details_list)` を返す。
- `tools.verify_predictions.get_actual_trifecta_from_race_data` / `get_odds_for_combination` は **domain.verification_models** から再エクスポートし、既存テストの import を壊さない。

予測・最適化についても、今後同様に「tools は application usecase を呼ぶだけ」に寄せる方針。

---

## 4. scripts の役割

- **scripts** は OS 依存の薄いラッパーに限定する（OS 非依存化方針に従う）。
- 行うこと: プロジェクトルートへの cd、venv 有効化、ログ出力先の指定、`python -m kyotei_predictor.cli.*` または `python -m kyotei_predictor.tools.*` の 1 回の起動。
- 行わないこと: INI のパースやビジネスロジック。詳細は `OS_PORTABILITY_STRATEGY.md` を参照。

---

## 5. OS 非依存構造との関係

- **CLI**（`python -m kyotei_predictor.cli.optimize` 等）が共通の実行入口となり、config と override で動作を制御する。
- **scripts** は OS ごとの違い（path、環境変数、python 起動）のみを担当し、処理本体は Python 側（CLI → tools → application）に集約する。
- CI / Mac / Windows / Linux では、同じ CLI コマンドで同じ処理を実行できることを目指す。詳細は `OS_PORTABILITY_STRATEGY.md` を参照。

---

## 6. 将来の B 案モデル追加方法

- **domain** に新しいデータ構造（例: 別の予測モデル用の候補型）やメトリクスを追加する。
- **application** に新しいユースケース（例: `evaluate_b_model_usecase.py`）を追加し、既存の infrastructure（config_loader, result_repository）を再利用する。
- **tools** に互換用の薄いエントリ（例: `tools.evaluate_b_model` が `application.evaluate_b_model_usecase.run` を呼ぶ）を追加する。
- **cli** にサブコマンド（例: `python -m kyotei_predictor.cli.evaluate_b`）を追加し、config と override で B 案用の設定を渡す。

これにより、既存の verify / predict / optimize の流れを壊さずに、B 案を層の上に載せて拡張できる。

---

## 参照

- 実行構造・CLI 設計: `CLI_DESIGN.md`, `OS_PORTABILITY_STRATEGY.md`
- プロジェクトレイアウト: `PROJECT_LAYOUT.md`, `ROADMAP_A_TO_B_BACKGROUND.md`
