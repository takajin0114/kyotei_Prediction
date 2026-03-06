"""
検証ユースケース: 予測JSON と race_data を照合し、的中率・回収率を算出する。

I/O は infrastructure、集計ロジックは domain に委譲。
tools.verify_predictions はこの run_verify を呼ぶ薄いラッパーとする。
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from kyotei_predictor.domain.verification_models import (
    get_actual_trifecta_from_race_data,
    get_odds_for_combination,
)
from kyotei_predictor.domain.metrics import aggregate_verification_to_summary
from kyotei_predictor.infrastructure.file_loader import load_json

# 1レースあたりの購入単価（円）。ROI 計算の基準。
BET_PER_COMBINATION = 100


def _load_odds_for_race(data_dir: Path, prediction_date: str, venue: str, rno: int) -> Optional[dict]:
    """指定レースのオッズJSONを読み、辞書で返す。存在しなければ None。"""
    odds_file = data_dir / f"odds_data_{prediction_date}_{venue}_R{rno}.json"
    if not odds_file.exists():
        return None
    return load_json(odds_file)


def run_verify(
    prediction_path: Path,
    data_dir: Path,
    evaluation_mode: str = "first_only",
) -> Tuple[Dict, List[Dict]]:
    """
    予測JSONと data_dir 内の race_data を照合し、集計結果とレース別詳細を返す。

    Args:
        prediction_path: 予測JSONのパス
        data_dir: race_data / odds_data が入ったディレクトリ
        evaluation_mode: "first_only"（1位のみ100円） または "selected_bets"（selected_bets の買い目で検証）

    Returns:
        (summary_dict, details_list) 既存 tools.verify_predictions と同じ形式。
    """
    pred = load_json(prediction_path)
    prediction_date = pred.get("prediction_date") or ""
    predictions = pred.get("predictions") or []
    data_dir = Path(data_dir)
    use_selected_bets = evaluation_mode == "selected_bets"

    # レースキー: (venue, race_number) -> (actual trifecta or None, odds or None)
    actual_and_odds: Dict[Tuple[str, int], Tuple[Optional[str], Optional[float]]] = {}
    for race in predictions:
        venue = race.get("venue") or ""
        rno = int(race.get("race_number") or 0)
        if not venue or rno <= 0:
            continue
        race_file = data_dir / f"race_data_{prediction_date}_{venue}_R{rno}.json"
        if not race_file.exists():
            continue
        race_data = load_json(race_file)
        actual = get_actual_trifecta_from_race_data(race_data)
        if actual is None:
            actual_and_odds[(venue, rno)] = (None, None)
            continue
        odds_file = data_dir / f"odds_data_{prediction_date}_{venue}_R{rno}.json"
        odds_ratio = None
        if odds_file.exists():
            odds_data = load_json(odds_file)
            odds_ratio = get_odds_for_combination(odds_data, actual)
        actual_and_odds[(venue, rno)] = (actual, odds_ratio)

    total = 0
    hit_rank1 = 0
    hit_top3 = 0
    hit_top10 = 0
    hit_top20 = 0
    total_bet = 0.0
    total_payout = 0.0
    total_payout_first = 0.0
    total_bet_selected = 0.0
    total_payout_selected = 0.0
    hit_count_selected = 0
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
        all_comb = race.get("all_combinations") or []
        comb_to_rank: Dict[str, int] = {}
        for i, c in enumerate(all_comb):
            comb = (c.get("combination") or "").strip()
            if comb:
                comb_to_rank[comb] = i + 1
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
        first_comb = (all_comb[0].get("combination") or "").strip() if all_comb else ""
        if first_comb == actual and odds_ratio is not None:
            total_payout_first += bet * odds_ratio

        detail = {
            "venue": venue,
            "race_number": rno,
            "actual": actual,
            "rank_in_top20": rank,
            "odds": odds_ratio,
            "hit_rank1": rank == 1,
            "hit_top3": rank is not None and rank <= 3,
            "hit_top10": rank is not None and rank <= 10,
            "hit_top20": rank is not None and rank <= 20,
            "evaluation_mode": evaluation_mode,
        }

        if use_selected_bets:
            selected = race.get("selected_bets") or []
            purchased_bets = len(selected)
            payout = 0.0
            if purchased_bets > 0 and actual is not None:
                odds_data = _load_odds_for_race(data_dir, prediction_date, venue, rno)
                for comb in selected:
                    c = (comb if isinstance(comb, str) else "").strip()
                    if not c:
                        continue
                    od = get_odds_for_combination(odds_data, c) if odds_data else None
                    if od is not None and c.replace(" ", "") == actual.replace(" ", ""):
                        payout += BET_PER_COMBINATION * od
                total_bet_selected += BET_PER_COMBINATION * purchased_bets
                total_payout_selected += payout
                if payout > 0:
                    hit_count_selected += 1
            detail["purchased_bets"] = purchased_bets
            detail["payout"] = round(payout, 2)
            detail["race_profit"] = round(payout - BET_PER_COMBINATION * purchased_bets, 2) if purchased_bets > 0 else 0.0

        details.append(detail)

    summary_obj = aggregate_verification_to_summary(
        prediction_file=str(prediction_path),
        prediction_date=prediction_date,
        data_dir=str(data_dir),
        races_with_result=total,
        hit_rank1=hit_rank1,
        hit_top3=hit_top3,
        hit_top10=hit_top10,
        hit_top20=hit_top20,
        total_bet=total_bet,
        total_payout=total_payout,
        total_payout_first=total_payout_first,
        total_bet_selected=total_bet_selected,
        total_payout_selected=total_payout_selected,
        hit_count_selected=hit_count_selected,
        evaluation_mode=evaluation_mode,
    )
    return summary_obj.to_dict(), details
