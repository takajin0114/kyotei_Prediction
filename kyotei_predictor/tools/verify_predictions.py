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
from typing import Dict, List, Optional, Tuple

# プロジェクトルート（kyotei_predictor の親＝outputs 等があるディレクトリ）
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_actual_trifecta_from_race_data(race_data: dict) -> Optional[str]:
    """
    race_data の race_records から 1-2-3 着の艇番を取得し "1-2-3" 形式で返す。
    着順が欠けている（null 等）場合は None。
    """
    records = race_data.get("race_records") or []
    if len(records) < 3:
        return None
    # arrival -> pit_number
    order_to_pit: Dict[int, int] = {}
    for r in records:
        arr = r.get("arrival")
        if arr is None:
            continue
        try:
            order_to_pit[int(arr)] = int(r.get("pit_number", 0))
        except (TypeError, ValueError):
            continue
    for k in (1, 2, 3):
        if k not in order_to_pit:
            return None
    return f"{order_to_pit[1]}-{order_to_pit[2]}-{order_to_pit[3]}"


def get_odds_for_combination(odds_data: dict, combination: str) -> Optional[float]:
    """オッズデータから指定 3連単のオッズ（倍率）を返す。"""
    for o in odds_data.get("odds_data") or []:
        c = o.get("combination") or ""
        if c.replace(" ", "") == combination.replace(" ", ""):
            r = o.get("ratio")
            return float(r) if r is not None else None
    return None


def run_verification(
    prediction_path: Path,
    data_dir: Path,
) -> Tuple[Dict, List[Dict]]:
    """
    予測JSONと data_dir 内の race_data を照合し、集計結果とレース別詳細を返す。
    """
    pred = _load_json(prediction_path)
    prediction_date = pred.get("prediction_date") or ""
    predictions = pred.get("predictions") or []
    data_dir = Path(data_dir)

    # レースキー: (venue, race_number) -> (actual trifecta or None, odds or None)
    actual_and_odds: Dict[Tuple[str, int], Tuple[Optional[str], Optional[float]]] = {}
    for race in predictions:
        venue = race.get("venue") or ""
        rno = int(race.get("race_number") or 0)
        if not venue or rno <= 0:
            continue
        # race_data: race_data_YYYY-MM-DD_VENUE_RN.json
        race_file = data_dir / f"race_data_{prediction_date}_{venue}_R{rno}.json"
        if not race_file.exists():
            continue
        race_data = _load_json(race_file)
        actual = get_actual_trifecta_from_race_data(race_data)
        if actual is None:
            actual_and_odds[(venue, rno)] = (None, None)
            continue
        odds_file = data_dir / f"odds_data_{prediction_date}_{venue}_R{rno}.json"
        odds_ratio = None
        if odds_file.exists():
            odds_data = _load_json(odds_file)
            odds_ratio = get_odds_for_combination(odds_data, actual)
        actual_and_odds[(venue, rno)] = (actual, odds_ratio)

    # 集計
    total = 0
    hit_rank1 = 0
    hit_top3 = 0
    hit_top10 = 0
    hit_top20 = 0
    total_bet = 0.0
    total_payout = 0.0
    total_payout_first = 0.0  # 1位予想に100円ずつ賭けた場合の払戻合計
    details: List[Dict] = []

    for race in predictions:
        venue = race.get("venue") or ""
        rno = int(race.get("race_number") or 0)
        key = (venue, rno)
        if key not in actual_and_odds:
            continue
        actual, odds_ratio = actual_and_odds[key]
        if actual is None:
            continue
        all_comb = (race.get("all_combinations") or [])
        comb_to_rank: Dict[str, int] = {}
        for i, c in enumerate(all_comb):
            comb = (c.get("combination") or "").strip()
            if comb:
                comb_to_rank[comb] = i + 1  # 1-origin rank
        rank = comb_to_rank.get(actual)
        total += 1
        if rank == 1:
            hit_rank1 += 1
        if rank is not None and rank <= 3:
            hit_top3 += 1
        if rank is not None and rank <= 10:
            hit_top10 += 1
        if rank is not None and rank <= 20:
            hit_top20 += 1
        bet = 100.0
        total_bet += bet
        if odds_ratio is not None and rank is not None:
            total_payout += bet * odds_ratio
        # 1位予想に賭けた場合の払戻（1位的中時のみ）
        first_comb = (all_comb[0].get("combination") or "").strip() if all_comb else ""
        if first_comb == actual and odds_ratio is not None:
            total_payout_first += bet * odds_ratio
        details.append({
            "venue": venue,
            "race_number": rno,
            "actual": actual,
            "rank_in_top20": rank,
            "odds": odds_ratio,
            "hit_rank1": rank == 1,
            "hit_top3": rank is not None and rank <= 3,
            "hit_top10": rank is not None and rank <= 10,
            "hit_top20": rank is not None and rank <= 20,
        })

    hit_rate_rank1 = (hit_rank1 / total * 100) if total else 0.0
    hit_rate_top3 = (hit_top3 / total * 100) if total else 0.0
    hit_rate_top10 = (hit_top10 / total * 100) if total else 0.0
    hit_rate_top20 = (hit_top20 / total * 100) if total else 0.0
    roi_actual = (total_payout / total_bet * 100) if total_bet else 0.0
    roi_our_first = (total_payout_first / total_bet * 100) if total_bet else 0.0

    # 評価ツール（metrics）と比較可能な共通キー（A/B比較・ログ標準化用）
    # hit_count: 的中件数, total_bet/total_payout: 投資額/払戻額, roi_pct: 回収率(%)
    summary = {
        "prediction_file": str(prediction_path),
        "prediction_date": prediction_date,
        "data_dir": str(data_dir),
        "races_with_result": total,
        "hit_rank1": hit_rank1,
        "hit_top3": hit_top3,
        "hit_top10": hit_top10,
        "hit_top20": hit_top20,
        "hit_rate_rank1_pct": round(hit_rate_rank1, 2),
        "hit_rate_top3_pct": round(hit_rate_top3, 2),
        "hit_rate_top10_pct": round(hit_rate_top10, 2),
        "hit_rate_top20_pct": round(hit_rate_top20, 2),
        "total_bet": total_bet,
        "total_payout_if_actual": round(total_payout, 2),
        "roi_pct_if_bet_actual": round(roi_actual, 2),
        "total_payout_our_1st": round(total_payout_first, 2),
        "roi_pct_our_1st": round(roi_our_first, 2),
        # 共通基盤: 評価 metrics と同じキーで比較可能（1位買いの場合）
        "hit_count": hit_rank1,
        "total_payout": round(total_payout_first, 2),
        "roi_pct": round(roi_our_first, 2),
        "evaluation_mode": "first_only",  # どの買い方で算出したか（将来 selected_bets 等と区別）
    }
    return summary, details


def main():
    parser = argparse.ArgumentParser(description="Verify prediction results (hit rate, ROI)")
    parser.add_argument("--prediction", "-p", type=str, default="outputs/predictions_latest.json",
                        help="Path to prediction JSON")
    parser.add_argument("--data-dir", "-d", type=str, default="kyotei_predictor/data/test_raw",
                        help="Directory containing race_data_*.json (and optionally odds_data_*.json)")
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

    summary, details = run_verification(pred_path, data_dir)

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

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = PROJECT_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "details": details}, f, ensure_ascii=False, indent=2)
        print(f"Wrote: {out_path}")

    # 検証ログ標準化: 推奨出力先に保存（--save）
    if args.save:
        out_dir = PROJECT_ROOT / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = out_dir / f"verification_{ts}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "details": details}, f, ensure_ascii=False, indent=2)
        print(f"Saved (--save): {save_path}")

    return 0


if __name__ == "__main__":
    exit(main())
