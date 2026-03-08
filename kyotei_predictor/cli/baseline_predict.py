"""
B案ベースラインの予測 CLI。

学習済みモデルと race_data_*.json のディレクトリを指定し、
A案と同一形式の予測 JSON を出力する。既存 verify_predictions で検証可能。
"""

import argparse
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from kyotei_predictor.infrastructure.path_manager import PROJECT_ROOT
from kyotei_predictor.application.baseline_predict_usecase import run_baseline_predict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="B案ベースラインで予測し、A案互換の JSON を出力する"
    )
    parser.add_argument("--predict-date", type=str, required=True, help="予測日 YYYY-MM-DD")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="race_data_*.json のディレクトリ。未指定時は kyotei_predictor/data/test_raw",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="学習済みモデルパス。未指定時は outputs/baseline_b_model.joblib",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="出力 JSON パス。未指定時は outputs/predictions_baseline_YYYY-MM-DD.json",
    )
    parser.add_argument(
        "--venues",
        type=str,
        default=None,
        help="対象会場（カンマ区切り）。未指定で全レース",
    )
    parser.add_argument(
        "--include-selected-bets",
        action="store_true",
        help="既存 betting_selector で selected_bets を付与（verify evaluation_mode=selected_bets 用）",
    )
    parser.add_argument("--strategy", type=str, default=None, help="買い目戦略。未指定時は config。single / top_n / top_n_ev（推奨）等")
    parser.add_argument("--top-n", type=int, default=None, help="strategy=top_n / top_n_ev の N。未指定時は config（推奨 5）")
    parser.add_argument("--score-threshold", type=float, default=None, help="strategy=threshold の閾値")
    parser.add_argument("--ev-threshold", type=float, default=None, help="strategy=ev / top_n_ev の閾値（expected_roi）。未指定時は config（推奨 1.15）")
    parser.add_argument(
        "--data-source",
        type=str,
        choices=("json", "db"),
        default=None,
        help="レースデータ読込元。未指定時は JSON 直読。オッズは data-dir から読む。",
    )
    parser.add_argument("--db-path", type=Path, default=None, help="data-source=db 時の SQLite パス")
    parser.add_argument(
        "--feature-set",
        type=str,
        choices=("current_features", "extended_features", "extended_features_v2"),
        default=None,
        help="特徴量セット。未指定時はモデル meta または環境変数。meta と不一致の場合は警告が出る。",
    )
    args = parser.parse_args()

    data_dir = args.data_dir or PROJECT_ROOT / "kyotei_predictor" / "data" / "test_raw"
    model_path = args.model_path or PROJECT_ROOT / "outputs" / "baseline_b_model.joblib"
    data_dir = Path(data_dir)
    model_path = Path(model_path)
    venues = [v.strip() for v in args.venues.split(",")] if args.venues else None

    if not model_path.exists():
        print(f"エラー: モデルが見つかりません: {model_path}")
        print("先に python -m kyotei_predictor.cli.baseline_train を実行してください。")
        return 1
    if args.data_source != "db" and not data_dir.is_dir():
        print(f"エラー: データディレクトリがありません: {data_dir}")
        return 1

    try:
        result = run_baseline_predict(
            model_path=model_path,
            data_dir=data_dir,
            prediction_date=args.predict_date,
            venues=venues,
            include_selected_bets=args.include_selected_bets,
            betting_strategy=args.strategy,
            betting_top_n=args.top_n,
            betting_score_threshold=args.score_threshold,
            betting_ev_threshold=args.ev_threshold,
            data_source=args.data_source,
            db_path=args.db_path,
            feature_set=args.feature_set,
        )
    except Exception as e:
        print(f"エラー: {e}")
        return 1

    out_path = args.output or PROJECT_ROOT / "outputs" / f"predictions_baseline_{args.predict_date}.json"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"予測結果を保存しました: {out_path}")
    print(f"レース数: {result['execution_summary']['total_races']}")
    print("検証する場合: python -m kyotei_predictor.tools.verify_predictions --prediction", out_path, "--data-dir", data_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
