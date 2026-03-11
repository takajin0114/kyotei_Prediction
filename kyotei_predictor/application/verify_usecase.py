"""
検証ユースケース: 予測JSON と race_data を照合し、的中率・回収率を算出する。

race_data は data_dir の JSON または repository（DB）から取得可能。
I/O は infrastructure、集計ロジックは domain に委譲。
"""

import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from kyotei_predictor.domain.verification_models import (
    get_actual_trifecta_from_race_data,
    get_odds_for_combination,
)
from kyotei_predictor.domain.metrics import aggregate_verification_to_summary
from kyotei_predictor.domain.repositories.race_data_repository import RaceDataRepositoryProtocol
from kyotei_predictor.infrastructure.file_loader import load_json

# 1レースあたりの購入単価（円）。ROI 計算の基準。
BET_PER_COMBINATION = 100

# confidence-weighted sizing: 既定の ev_gap / prob_gap 閾値
DEFAULT_EV_GAP_HIGH = 0.10
DEFAULT_EV_GAP_MID = 0.07
DEFAULT_PROB_GAP_HIGH = 0.05


def _ev_gap_and_prob_gap_from_combinations(
    all_comb: List[dict],
) -> Tuple[Optional[float], Optional[float]]:
    """
    all_combinations から ev_rank1 - ev_rank2 (ev_gap) と
    prob_rank1 - prob_rank2 (pred_prob_gap) を計算する。
    EV = probability * ratio。ソートして上位2件の差を返す。
    """
    if not all_comb:
        return None, None
    ev_list: List[Tuple[float, float]] = []
    for c in all_comb:
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        ev = prob * ratio
        ev_list.append((ev, prob))
    if len(ev_list) < 2:
        return None, None
    ev_list.sort(key=lambda x: -x[0])
    ev_gap = ev_list[0][0] - ev_list[1][0]
    prob_gap = ev_list[0][1] - ev_list[1][1]
    return ev_gap, prob_gap


def _unit_size_for_race(
    ev_gap: Optional[float],
    pred_prob_gap: Optional[float],
    bet_sizing_mode: str,
    config: Optional[Dict[str, float]] = None,
) -> float:
    """
    confidence-weighted fixed sizing: レースの ev_gap / pred_prob_gap に応じて
    ベット単位 (1.0 = 100円, 0.5 = 50円相当) を返す。
    bet_sizing_mode: "fixed" | "confidence_weighted_ev_gap_v1" | "confidence_weighted_ev_gap_v2" | "confidence_weighted_prob_gap_v1"
    """
    if bet_sizing_mode is None or (isinstance(bet_sizing_mode, str) and bet_sizing_mode.strip().lower() == "fixed"):
        return 1.0
    mode = (bet_sizing_mode or "fixed").strip().lower()
    cfg = config or {}
    if mode == "fixed":
        return 1.0
    if mode == "confidence_weighted_ev_gap_v1":
        # high: 1.0, normal: 0.5
        high = float(cfg.get("ev_gap_high", DEFAULT_EV_GAP_HIGH))
        if ev_gap is not None and ev_gap >= high:
            return 1.0
        return float(cfg.get("normal_unit", 0.5))
    if mode == "confidence_weighted_ev_gap_v2":
        # high: 1.0, mid: 0.75, normal: 0.5
        high = float(cfg.get("ev_gap_high", DEFAULT_EV_GAP_HIGH))
        mid = float(cfg.get("ev_gap_mid", DEFAULT_EV_GAP_MID))
        if ev_gap is not None and ev_gap >= high:
            return 1.0
        if ev_gap is not None and ev_gap >= mid:
            return float(cfg.get("mid_unit", 0.75))
        return float(cfg.get("normal_unit", 0.5))
    if mode == "confidence_weighted_prob_gap_v1":
        # high: 1.0, normal: 0.5 (pred_prob_gap ベース)
        high = float(cfg.get("prob_gap_high", DEFAULT_PROB_GAP_HIGH))
        if pred_prob_gap is not None and pred_prob_gap >= high:
            return 1.0
        return float(cfg.get("normal_unit", 0.5))
    return 1.0


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
    data_source: Optional[str] = None,
    race_repository: Optional[RaceDataRepositoryProtocol] = None,
    db_path: Optional[Union[str, Path]] = None,
    bet_sizing_mode: Optional[str] = None,
    bet_sizing_config: Optional[Dict[str, float]] = None,
) -> Tuple[Dict, List[Dict]]:
    """
    予測JSONと race_data を照合し、集計結果とレース別詳細を返す。
    race_data は data_dir の JSON または repository（data_source=db）から取得。

    Args:
        prediction_path: 予測JSONのパス
        data_dir: race_data / odds_data が入ったディレクトリ（JSON 時）。オッズはここから読む。
        evaluation_mode: "first_only" または "selected_bets"
        data_source: "json" | "db" | None。None のときは data_dir の JSON 直読。
        race_repository: 指定時はこのリポジトリで race_data 取得。
        db_path: data_source=db 時の SQLite パス。
        bet_sizing_mode: "fixed" | "confidence_weighted_ev_gap_v1" | "confidence_weighted_ev_gap_v2" | "confidence_weighted_prob_gap_v1"。selected_bets 時のみ有効。
        bet_sizing_config: 閾値等（ev_gap_high, ev_gap_mid, prob_gap_high, normal_unit, mid_unit）。None で既定値。

    Returns:
        (summary_dict, details_list) 既存 tools.verify_predictions と同じ形式。
    """
    pred = load_json(prediction_path)
    prediction_date = pred.get("prediction_date") or ""
    predictions = pred.get("predictions") or []
    data_dir = Path(data_dir)
    use_selected_bets = evaluation_mode == "selected_bets"

    repo: Optional[RaceDataRepositoryProtocol] = race_repository
    if repo is None and data_source and data_source.strip().lower() == "db":
        from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
            get_race_data_repository,
        )
        repo = get_race_data_repository(
            "db",
            data_dir=data_dir,
            db_path=str(db_path) if db_path else None,
        )

    # レースキー: (venue, race_number) -> (actual trifecta or None, odds or None)
    actual_and_odds: Dict[Tuple[str, int], Tuple[Optional[str], Optional[float]]] = {}
    for race in predictions:
        venue = race.get("venue") or ""
        rno = int(race.get("race_number") or 0)
        if not venue or rno <= 0:
            continue
        if repo is not None:
            race_data = repo.load_race(prediction_date, venue, rno)
        else:
            race_file = data_dir / f"race_data_{prediction_date}_{venue}_R{rno}.json"
            if not race_file.exists():
                continue
            try:
                race_data = load_json(race_file)
            except Exception:
                continue
        if race_data is None:
            continue
        actual = get_actual_trifecta_from_race_data(race_data)
        if actual is None:
            actual_and_odds[(venue, rno)] = (None, None)
            continue
        odds_ratio = None
        if repo is not None and hasattr(repo, "get_odds"):
            odds_data = repo.get_odds(prediction_date, venue, rno)
        else:
            odds_data = _load_odds_for_race(data_dir, prediction_date, venue, rno)
        if odds_data is not None:
            try:
                odds_ratio = get_odds_for_combination(odds_data, actual)
            except Exception:
                pass
        actual_and_odds[(venue, rno)] = (actual, odds_ratio)

    # 再現性診断用カウント（Task 5）
    races_with_predictions = len(predictions)
    races_with_odds = sum(1 for v in actual_and_odds.values() if v[1] is not None)
    skip_result_missing = 0
    skip_odds_missing = 0
    skip_no_ev_candidate = 0
    skipped_identifiers: Dict[str, List[str]] = {
        "result_missing": [],
        "odds_missing": [],
        "no_ev_candidate": [],
    }
    selected_bets_race_count = 0
    bets_per_date: Dict[str, int] = {}

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
    selected_bets_count = 0  # 組み合わせ数（weighted でもカウントは同一）
    sum_log_loss = 0.0
    sum_brier = 0.0
    n_prob_races = 0
    details: List[Dict] = []

    for race in predictions:
        venue = race.get("venue") or ""
        rno = int(race.get("race_number") or 0)
        key = (venue, rno)
        ident = f"{venue}_R{rno}" if venue else ""
        if key not in actual_and_odds:
            skip_result_missing += 1
            if ident:
                skipped_identifiers["result_missing"].append(ident)
            continue
        actual, odds_ratio = actual_and_odds[key]
        if actual is None:
            skip_result_missing += 1
            if ident:
                skipped_identifiers["result_missing"].append(ident)
            continue
        if odds_ratio is None:
            skip_odds_missing += 1
            if ident:
                skipped_identifiers["odds_missing"].append(ident)
        selected = race.get("selected_bets") or []
        if use_selected_bets and len(selected) == 0:
            skip_no_ev_candidate += 1
            if ident:
                skipped_identifiers["no_ev_candidate"].append(ident)
        if len(selected) > 0:
            selected_bets_race_count += 1
        all_comb = race.get("all_combinations") or []
        comb_to_rank: Dict[str, int] = {}
        prob_actual = None
        actual_norm = (actual or "").replace(" ", "")
        for i, c in enumerate(all_comb):
            comb_raw = (c.get("combination") or "").strip()
            if comb_raw:
                comb_to_rank[comb_raw] = i + 1
                if comb_raw.replace(" ", "") == actual_norm:
                    prob_actual = float(c.get("probability", 0.0))
        if prob_actual is not None:
            p = max(prob_actual, 1e-15)
            sum_log_loss += -math.log(p)
            sum_brier += (1.0 - prob_actual) ** 2
            n_prob_races += 1
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
            ev_gap, pred_prob_gap = _ev_gap_and_prob_gap_from_combinations(all_comb)
            unit = _unit_size_for_race(
                ev_gap, pred_prob_gap,
                bet_sizing_mode or "fixed",
                bet_sizing_config,
            )
            bet_per_bet = unit * BET_PER_COMBINATION
            payout = 0.0
            if purchased_bets > 0 and actual is not None:
                if repo is not None and hasattr(repo, "get_odds"):
                    odds_data = repo.get_odds(prediction_date, venue, rno)
                else:
                    odds_data = _load_odds_for_race(data_dir, prediction_date, venue, rno)
                for comb in selected:
                    c = (comb if isinstance(comb, str) else "").strip()
                    if not c:
                        continue
                    od = get_odds_for_combination(odds_data, c) if odds_data else None
                    if od is not None and c.replace(" ", "") == actual.replace(" ", ""):
                        payout += bet_per_bet * od
                total_bet_selected += bet_per_bet * purchased_bets
                total_payout_selected += payout
                if payout > 0:
                    hit_count_selected += 1
            selected_bets_count += purchased_bets
            detail["purchased_bets"] = purchased_bets
            detail["payout"] = round(payout, 2)
            detail["race_profit"] = round(payout - bet_per_bet * purchased_bets, 2) if purchased_bets > 0 else 0.0

        details.append(detail)

    # 組み合わせ数（fixed のときは total_bet_selected/100 と一致。weighted では別途カウント）
    selected_bets_total_count = selected_bets_count
    if prediction_date:
        bets_per_date[prediction_date] = selected_bets_total_count

    # skipped = 結果がなくて評価しなかったレースのみ。odds_missing / no_ev_candidate は評価したが bet しなかった件数
    skipped_race_count = skip_result_missing
    evaluated_race_count = total
    races_with_selected_bets = selected_bets_race_count

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
    summary_dict = summary_obj.to_dict()
    # 再現性診断用: verify 前提条件を summary に追加（Task 5）
    summary_dict["evaluated_race_count"] = evaluated_race_count
    summary_dict["races_with_predictions"] = races_with_predictions
    summary_dict["races_with_odds"] = races_with_odds
    summary_dict["races_with_selected_bets"] = races_with_selected_bets
    summary_dict["skipped_race_count"] = skipped_race_count
    summary_dict["skip_reasons"] = {
        "odds_missing": skip_odds_missing,
        "prediction_missing": 0,
        "no_ev_candidate": skip_no_ev_candidate,
        "result_missing": skip_result_missing,
    }
    summary_dict["selected_bets_total_count"] = selected_bets_total_count
    summary_dict["total_staked"] = round(total_bet_selected, 2)
    summary_dict["total_profit"] = round(total_payout_selected - total_bet_selected, 2) if total_bet_selected else 0.0
    summary_dict["average_bet_size"] = round(total_bet_selected / selected_bets_total_count, 2) if selected_bets_total_count else 0.0
    summary_dict["profit_per_1000_bets"] = round(1000.0 * (total_payout_selected - total_bet_selected) / selected_bets_total_count, 2) if selected_bets_total_count else 0.0
    summary_dict["bets_per_date"] = bets_per_date
    summary_dict["odds_missing_count"] = skip_odds_missing  # conditions で参照する用
    summary_dict["skipped_race_identifiers"] = skipped_identifiers
    if n_prob_races > 0:
        summary_dict["log_loss"] = round(sum_log_loss / n_prob_races, 6)
        summary_dict["brier_score"] = round(sum_brier / n_prob_races, 6)
        summary_dict["n_races_for_log_loss_brier"] = n_prob_races
    return summary_dict, details
