"""
評価メトリクスの純粋計算（ROI・的中率・報酬集約）。

I/O なし。tools.evaluation.metrics と役割を共有しつつ、
domain では dataclass と関数で表現する。
TODO: 段階的に tools.evaluation.metrics から呼び出す形に寄せる。
"""

from dataclasses import dataclass
from typing import List


def compute_roi_pct(total_payout: float, total_bet: float) -> float:
    """回収率（%）を計算。total_bet が 0 のときは 0.0。"""
    if total_bet <= 0:
        return 0.0
    return round(total_payout / total_bet * 100.0, 2)


def compute_hit_rate_pct(hit_count: int, total_races: int) -> float:
    """的中率（%）を計算。total_races が 0 のときは 0.0。"""
    if total_races <= 0:
        return 0.0
    return round(hit_count / total_races * 100.0, 2)


@dataclass
class TrialMetrics:
    """1トライアル分の評価指標（学習・Optuna 用）。"""
    hit_rate: float
    mean_reward: float
    roi_pct: float
    total_bet: float
    total_payout: float
    hit_count: int
    n_episodes: int

    def to_dict(self) -> dict:
        return {
            "hit_rate": self.hit_rate,
            "mean_reward": self.mean_reward,
            "roi_pct": self.roi_pct,
            "total_bet": self.total_bet,
            "total_payout": self.total_payout,
            "hit_count": self.hit_count,
            "n_episodes": self.n_episodes,
        }


def aggregate_verification_to_summary(
    prediction_file: str,
    prediction_date: str,
    data_dir: str,
    races_with_result: int,
    hit_rank1: int,
    hit_top3: int,
    hit_top10: int,
    hit_top20: int,
    total_bet: float,
    total_payout: float,
    total_payout_first: float,
    total_bet_selected: float,
    total_payout_selected: float,
    hit_count_selected: int,
    evaluation_mode: str,
) -> "VerificationSummary":
    """
    検証の集計値から VerificationSummary を組み立てる。純粋関数。
    """
    from kyotei_predictor.domain.verification_models import VerificationSummary

    hit_rate_rank1 = compute_hit_rate_pct(hit_rank1, races_with_result)
    hit_rate_top3 = compute_hit_rate_pct(hit_top3, races_with_result)
    hit_rate_top10 = compute_hit_rate_pct(hit_top10, races_with_result)
    hit_rate_top20 = compute_hit_rate_pct(hit_top20, races_with_result)
    roi_actual = compute_roi_pct(total_payout, total_bet) if total_bet else 0.0
    roi_our_first = compute_roi_pct(total_payout_first, total_bet) if total_bet else 0.0
    use_selected = evaluation_mode == "selected_bets" and total_bet_selected > 0
    roi_pct_final = (
        compute_roi_pct(total_payout_selected, total_bet_selected)
        if use_selected
        else roi_our_first
    )
    hit_count = hit_count_selected if use_selected else hit_rank1
    total_payout_final = total_payout_selected if use_selected else total_payout_first
    total_bet_final = total_bet_selected if use_selected else total_bet

    return VerificationSummary(
        prediction_file=prediction_file,
        prediction_date=prediction_date,
        data_dir=data_dir,
        races_with_result=races_with_result,
        hit_rank1=hit_rank1,
        hit_top3=hit_top3,
        hit_top10=hit_top10,
        hit_top20=hit_top20,
        hit_rate_rank1_pct=hit_rate_rank1,
        hit_rate_top3_pct=hit_rate_top3,
        hit_rate_top10_pct=hit_rate_top10,
        hit_rate_top20_pct=hit_rate_top20,
        total_bet=total_bet_final,
        total_payout_if_actual=round(total_payout, 2),
        roi_pct_if_bet_actual=roi_actual,
        total_payout_our_1st=round(total_payout_first, 2),
        roi_pct_our_1st=roi_our_first,
        hit_count=hit_count,
        total_payout=round(total_payout_final, 2),
        roi_pct=roi_pct_final,
        evaluation_mode=evaluation_mode,
        total_bet_selected=total_bet_selected,
        total_payout_selected=round(total_payout_selected, 2),
    )
