"""
EV 戦略まわりの betting モジュール。

- expected_value: EV（期待リターン）計算
- bet_sizing: fixed / Kelly ベットサイズ
- bankroll_simulation: 資金曲線・ドローダウン・Sharpe
"""

from kyotei_predictor.betting.expected_value import (
    expected_roi,
    ev_above_threshold,
)
from kyotei_predictor.betting.kelly import kelly_capped
from kyotei_predictor.betting.bet_sizing import (
    kelly_fraction,
    compute_stake,
    BET_SIZING_FIXED,
    BET_SIZING_KELLY_FULL,
    BET_SIZING_KELLY_HALF,
    BET_SIZING_KELLY_CAPPED,
)
from kyotei_predictor.betting.bankroll_simulation import (
    simulate_bankroll,
    build_bet_list_from_verify,
)

__all__ = [
    "expected_roi",
    "ev_above_threshold",
    "kelly_fraction",
    "kelly_capped",
    "compute_stake",
    "BET_SIZING_FIXED",
    "BET_SIZING_KELLY_FULL",
    "BET_SIZING_KELLY_HALF",
    "BET_SIZING_KELLY_CAPPED",
    "simulate_bankroll",
    "build_bet_list_from_verify",
]
