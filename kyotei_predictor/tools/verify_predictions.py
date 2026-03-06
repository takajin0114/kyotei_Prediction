#!/usr/bin/env python3
"""
予測結果の検証スクリプト（的中率・回収率）

学習データと同じ日・会場の race_data に着順が含まれている場合、
予測JSONと照合して 1位的中率 / Top3・Top10・Top20 的中率、
およびオッズがある場合は回収率を算出する。

標準出力形式（A/B比較用）:
  summary に hit_count, total_bet, total_payout, roi_pct を含める。
  評価ツール（evaluate_graduated_reward_model）の metrics と同一キーで比較可能。
  推奨出力先: outputs/verification_YYYYMMDD_HHMMSS.json（--save で自動作成）。

使い方:
  python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --data-dir kyotei_predictor/data/test_raw
  python -m kyotei_predictor.tools.verify_predictions --prediction outputs/predictions_2024-05-01.json --save
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# プロジェクトルート（kyotei_predictor の親＝outputs 等があるディレクトリ）
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# config から evaluation_mode を読む（CLI 未指定時用）
def _get_config_evaluation_mode() -> str:
    """ImprovementConfigManager の evaluation_mode。未読込時は first_only。"""
    try:
        from kyotei_predictor.config.improvement_config_manager import ImprovementConfigManager
        return ImprovementConfigManager().get_evaluation_mode()
    except Exception:
        return "first_only"


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_verification_payload(path: Union[Path, str]) -> Tuple[Dict, List[Dict]]:
    """
    検証 JSON ファイルを読み、summary と details を返す。
    新旧どちらの形式（トップに evaluation_mode あり/なし）でも同じように参照できる後方互換ヘルパー。

    Args:
        path: 検証 JSON のパス（--output / --save で保存したファイル）。

    Returns:
        (summary, details) のタプル。
    """
    payload = _load_json(Path(path))
    return (payload.get("summary", {}), payload.get("details", []))


# 互換レイヤー: domain の純粋関数を再エクスポート（既存テスト・他モジュールの import を壊さない）
from kyotei_predictor.domain.verification_models import (
    get_actual_trifecta_from_race_data,
    get_odds_for_combination,
)

# 検証実行は application 層に委譲
def run_verification(
    prediction_path: Path,
    data_dir: Path,
    evaluation_mode: str = "first_only",
) -> Tuple[Dict, List[Dict]]:
    """
    予測JSONと data_dir 内の race_data を照合し、集計結果とレース別詳細を返す。
    実装は application.verify_usecase.run_verify に委譲する。
    """
    from kyotei_predictor.application.verify_usecase import run_verify
    return run_verify(prediction_path, data_dir, evaluation_mode=evaluation_mode)


def main():
    parser = argparse.ArgumentParser(description="Verify prediction results (hit rate, ROI)")
    parser.add_argument("--prediction", "-p", type=str, default="outputs/predictions_latest.json",
                        help="Path to prediction JSON")
    parser.add_argument("--data-dir", "-d", type=str, default="kyotei_predictor/data/test_raw",
                        help="Directory containing race_data_*.json (and optionally odds_data_*.json)")
    parser.add_argument("--evaluation-mode", type=str, choices=("first_only", "selected_bets"), default=None,
                        help="検証モード。未指定時は config の evaluation_mode を使用（config 未設定時は first_only）")
    parser.add_argument("--output", "-o", type=str, help="Optional: write summary+details JSON to this path")
    parser.add_argument("--save", action="store_true",
                        help="Save result to outputs/verification_YYYYMMDD_HHMMSS.json (A/B比較用推奨)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-race details")
    args = parser.parse_args()

    pred_path = Path(args.prediction)
    if not pred_path.is_absolute():
        pred_path = PROJECT_ROOT / pred_path
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    if not pred_path.exists():
        print(f"Prediction file not found: {pred_path}")
        return 1
    if not data_dir.is_dir():
        print(f"Data directory not found: {data_dir}")
        return 1

    # CLI 指定があれば優先、未指定時は config の evaluation_mode（従来互換: first_only）
    evaluation_mode_source = "cli" if args.evaluation_mode is not None else "config"
    evaluation_mode = args.evaluation_mode if args.evaluation_mode is not None else _get_config_evaluation_mode()
    if evaluation_mode not in ("first_only", "selected_bets"):
        evaluation_mode = "first_only"
    # 比較条件の追跡: 実行時ログに evaluation_mode と由来を1行で出す
    print(f"evaluation_mode={evaluation_mode} source={evaluation_mode_source}")
    summary, details = run_verification(pred_path, data_dir, evaluation_mode=evaluation_mode)
    summary["evaluation_mode_source"] = evaluation_mode_source  # 保存JSONで比較条件の由来を追跡

    print("=== Verification ===")
    print(f"Prediction: {summary['prediction_file']}")
    print(f"Date: {summary['prediction_date']}  Data dir: {summary['data_dir']}")
    print(f"Races with result: {summary['races_with_result']}")
    print(f"Hit rate (1st):  {summary['hit_rank1']}/{summary['races_with_result']} = {summary['hit_rate_rank1_pct']}%")
    print(f"Hit rate (Top3): {summary['hit_top3']}/{summary['races_with_result']} = {summary['hit_rate_top3_pct']}%")
    print(f"Hit rate (Top10): {summary['hit_top10']}/{summary['races_with_result']} = {summary['hit_rate_top10_pct']}%")
    print(f"Hit rate (Top20): {summary['hit_top20']}/{summary['races_with_result']} = {summary['hit_rate_top20_pct']}%")
    print(f"Total bet (100/race): {summary['total_bet']:.0f}")
    print(f"ROI (bet on 1st prediction): {summary['roi_pct_our_1st']}%  payout={summary['total_payout_our_1st']}")
    print(f"Reference (if bet on actual): ROI {summary['roi_pct_if_bet_actual']}%  payout={summary['total_payout_if_actual']}")

    if args.verbose:
        print("\n--- Per-race ---")
        for d in details:
            print(f"  {d['venue']} R{d['race_number']}: actual={d['actual']} rank={d['rank_in_top20']} hit_1st={d['hit_rank1']} top3={d['hit_top3']}")

    # 保存JSON: 比較条件を固定するため summary / details / トップレベルに evaluation_mode を必ず含める
    output_payload = {
        "evaluation_mode": summary["evaluation_mode"],
        "summary": summary,
        "details": details,
    }
    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, ensure_ascii=False, indent=2)
        print(f"Wrote: {out_path}")

    # 検証ログ標準化: 推奨出力先に保存（--save）
    if args.save:
        out_dir = PROJECT_ROOT / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = out_dir / f"verification_{ts}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, ensure_ascii=False, indent=2)
        print(f"Saved (--save): {save_path}")

    return 0


if __name__ == "__main__":
    exit(main())
