"""
DB 由来の選手履歴（直近N走・場別成績）を取得し、recent_form / venue_course 特徴量用の統計を計算する。
リーク防止: 対象レースより前の履歴のみ使用する。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# 直近N走の N（デフォルト 5）
RECENT_N = 5
# 場別の最小サンプル
VENUE_MIN_N = 1


def _arrival_from_records(race_data: Dict[str, Any], pit_number: int) -> Optional[int]:
    """race_records から pit_number の着順（1-6）を返す。無ければ None。"""
    for r in race_data.get("race_records") or []:
        if r.get("pit_number") == pit_number:
            a = r.get("arrival")
            if a is not None:
                try:
                    return int(a)
                except (TypeError, ValueError):
                    pass
            return None
    return None


def get_racer_history_from_db(
    db_path: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_races: Optional[int] = None,
) -> List[Tuple[str, str, str, int]]:
    """
    DB を走査し、(registration_number, race_date, stadium, arrival) のリストを返す。
    日付昇順。予測時は date_to を対象日より前にすること。
    """
    from kyotei_predictor.data.race_db import RaceDB

    db = RaceDB(db_path)
    pairs = db.get_race_odds_pairs(date_from=date_from, date_to=date_to)
    if max_races is not None:
        pairs = pairs[:max_races]
    out: List[Tuple[str, str, str, int]] = []
    for rd, stadium, race_number in pairs:
        if date_to is not None and rd >= date_to:
            continue
        race_data = db.get_race_json(rd, stadium, race_number)
        if not race_data:
            continue
        entries = race_data.get("race_entries") or []
        for entry in entries[:6]:
            reg_no = entry.get("racer", {}).get("registration_number")
            if reg_no is None:
                reg_no = ""
            try:
                reg_no = str(reg_no).strip()
            except Exception:
                reg_no = ""
            pit = entry.get("pit_number", 0)
            arrival = _arrival_from_records(race_data, pit)
            if arrival is None:
                continue
            out.append((reg_no, rd, stadium, arrival))
    out.sort(key=lambda x: (x[1], x[2], x[3]))
    return out


def compute_recent_form(
    history: List[Tuple[str, str, str, int]],
    registration_number: str,
    as_of_date: str,
    n: int = RECENT_N,
) -> Tuple[float, float, float, int]:
    """
    対象選手の「as_of_date より前」の直近 n 走から統計を計算。
    Returns:
        (avg_rank_norm, rate_1st, rate_top3, sample_size)
        avg_rank_norm: 平均着順を 1-6 で正規化（1着=1.0, 6着=0.0）
        rate_1st: 1着率 (0-1)
        rate_top3: 3着内率 (0-1)
        sample_size: 元になった走数
    履歴不足時は (0.5, 0.0, 0.0, 0) で防御。
    """
    reg = (registration_number or "").strip()
    past = [(d, s, a) for (r, d, s, a) in history if r == reg and d < as_of_date]
    past.sort(key=lambda x: x[0])
    last_n = past[-n:] if len(past) >= n else past
    if not last_n:
        return (0.5, 0.0, 0.0, 0)
    arrivals = [a for (_, _, a) in last_n]
    avg_rank = sum(arrivals) / len(arrivals)
    avg_norm = 1.0 - (avg_rank - 1) / 5.0 if avg_rank else 0.5
    avg_norm = max(0.0, min(1.0, avg_norm))
    rate_1st = sum(1 for a in arrivals if a == 1) / len(arrivals)
    rate_top3 = sum(1 for a in arrivals if a <= 3) / len(arrivals)
    return (round(avg_norm, 4), round(rate_1st, 4), round(rate_top3, 4), len(last_n))


def compute_venue_form(
    history: List[Tuple[str, str, str, int]],
    registration_number: str,
    as_of_date: str,
    stadium: str,
    n: int = 10,
) -> Tuple[float, float, int]:
    """
    対象選手の「as_of_date より前」の当該場での成績。
    Returns:
        (avg_rank_norm, rate_1st, sample_size)
    履歴不足時は (0.5, 0.0, 0)。
    """
    reg = (registration_number or "").strip()
    past = [
        (d, a)
        for (r, d, s, a) in history
        if r == reg and d < as_of_date and (s or "").strip() == (stadium or "").strip()
    ]
    past.sort(key=lambda x: x[0])
    last_n = past[-n:] if len(past) >= n else past
    if not last_n:
        return (0.5, 0.0, 0)
    arrivals = [a for (_, a) in last_n]
    avg_rank = sum(arrivals) / len(arrivals)
    avg_norm = 1.0 - (avg_rank - 1) / 5.0 if avg_rank else 0.5
    avg_norm = max(0.0, min(1.0, avg_norm))
    rate_1st = sum(1 for a in arrivals if a == 1) / len(arrivals)
    return (round(avg_norm, 4), round(rate_1st, 4), len(last_n))
