"""
検証まわりのドメインモデル（純粋なデータ構造）。

予測・検証結果を dataclass で表現し、dict との相互変換で既存コードと互換を保つ。
I/O は行わない。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VerificationDetail:
    """1レース分の検証詳細（的中・順位・払戻など）。"""
    venue: str
    race_number: int
    actual: Optional[str]
    rank_in_top20: Optional[int]
    odds: Optional[float]
    hit_rank1: bool
    hit_top3: bool
    hit_top10: bool
    hit_top20: bool
    evaluation_mode: str = "first_only"
    purchased_bets: int = 0
    payout: float = 0.0
    race_profit: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "venue": self.venue,
            "race_number": self.race_number,
            "actual": self.actual,
            "rank_in_top20": self.rank_in_top20,
            "odds": self.odds,
            "hit_rank1": self.hit_rank1,
            "hit_top3": self.hit_top3,
            "hit_top10": self.hit_top10,
            "hit_top20": self.hit_top20,
            "evaluation_mode": self.evaluation_mode,
            "purchased_bets": self.purchased_bets,
            "payout": round(self.payout, 2),
            "race_profit": round(self.race_profit, 2),
        }


@dataclass
class VerificationSummary:
    """
    検証サマリ（的中率・回収率・投資額・払戻額など）。

    評価ツール（evaluate_graduated_reward_model）の metrics と同一キーで比較可能。
    """
    prediction_file: str
    prediction_date: str
    data_dir: str
    races_with_result: int
    hit_rank1: int
    hit_top3: int
    hit_top10: int
    hit_top20: int
    hit_rate_rank1_pct: float
    hit_rate_top3_pct: float
    hit_rate_top10_pct: float
    hit_rate_top20_pct: float
    total_bet: float
    total_payout_if_actual: float
    roi_pct_if_bet_actual: float
    total_payout_our_1st: float
    roi_pct_our_1st: float
    hit_count: int
    total_payout: float
    roi_pct: float
    evaluation_mode: str
    total_bet_selected: float = 0.0
    total_payout_selected: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "prediction_file": self.prediction_file,
            "prediction_date": self.prediction_date,
            "data_dir": self.data_dir,
            "races_with_result": self.races_with_result,
            "hit_rank1": self.hit_rank1,
            "hit_top3": self.hit_top3,
            "hit_top10": self.hit_top10,
            "hit_top20": self.hit_top20,
            "hit_rate_rank1_pct": round(self.hit_rate_rank1_pct, 2),
            "hit_rate_top3_pct": round(self.hit_rate_top3_pct, 2),
            "hit_rate_top10_pct": round(self.hit_rate_top10_pct, 2),
            "hit_rate_top20_pct": round(self.hit_rate_top20_pct, 2),
            "total_bet": self.total_bet,
            "total_payout_if_actual": round(self.total_payout_if_actual, 2),
            "roi_pct_if_bet_actual": round(self.roi_pct_if_bet_actual, 2),
            "total_payout_our_1st": round(self.total_payout_our_1st, 2),
            "roi_pct_our_1st": round(self.roi_pct_our_1st, 2),
            "hit_count": self.hit_count,
            "total_payout": round(self.total_payout, 2),
            "roi_pct": self.roi_pct,
            "evaluation_mode": self.evaluation_mode,
        }
        if self.total_bet_selected > 0 or self.total_payout_selected > 0:
            d["total_bet_selected"] = self.total_bet_selected
            d["total_payout_selected"] = round(self.total_payout_selected, 2)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VerificationSummary":
        return cls(
            prediction_file=d.get("prediction_file", ""),
            prediction_date=d.get("prediction_date", ""),
            data_dir=d.get("data_dir", ""),
            races_with_result=int(d.get("races_with_result", 0)),
            hit_rank1=int(d.get("hit_rank1", 0)),
            hit_top3=int(d.get("hit_top3", 0)),
            hit_top10=int(d.get("hit_top10", 0)),
            hit_top20=int(d.get("hit_top20", 0)),
            hit_rate_rank1_pct=float(d.get("hit_rate_rank1_pct", 0)),
            hit_rate_top3_pct=float(d.get("hit_rate_top3_pct", 0)),
            hit_rate_top10_pct=float(d.get("hit_rate_top10_pct", 0)),
            hit_rate_top20_pct=float(d.get("hit_rate_top20_pct", 0)),
            total_bet=float(d.get("total_bet", 0)),
            total_payout_if_actual=float(d.get("total_payout_if_actual", 0)),
            roi_pct_if_bet_actual=float(d.get("roi_pct_if_bet_actual", 0)),
            total_payout_our_1st=float(d.get("total_payout_our_1st", 0)),
            roi_pct_our_1st=float(d.get("roi_pct_our_1st", 0)),
            hit_count=int(d.get("hit_count", 0)),
            total_payout=float(d.get("total_payout", 0)),
            roi_pct=float(d.get("roi_pct", 0)),
            evaluation_mode=d.get("evaluation_mode", "first_only"),
            total_bet_selected=float(d.get("total_bet_selected", 0)),
            total_payout_selected=float(d.get("total_payout_selected", 0)),
        )


def get_actual_trifecta_from_race_data(race_data: dict) -> Optional[str]:
    """
    race_data の race_records から 1-2-3 着の艇番を取得し "1-2-3" 形式で返す。
    着順が欠けている（null 等）場合は None。純粋関数（I/O なし）。
    """
    records = race_data.get("race_records") or []
    if len(records) < 3:
        return None
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
    """オッズデータから指定 3連単のオッズ（倍率）を返す。純粋関数。"""
    for o in odds_data.get("odds_data") or []:
        c = o.get("combination") or ""
        if c.replace(" ", "") == combination.replace(" ", ""):
            r = o.get("ratio")
            return float(r) if r is not None else None
    return None
