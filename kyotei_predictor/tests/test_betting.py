"""
betting モジュールの単体テスト（EV 計算・Kelly・資金シミュレーション）。
"""

import pytest


def test_expected_roi():
    from kyotei_predictor.betting.expected_value import expected_roi, ev_above_threshold
    assert expected_roi(0.1, 15) == 1.5
    assert expected_roi(0.05, 20) == 1.0
    assert ev_above_threshold(0.1, 15, 1.0) is True
    assert ev_above_threshold(0.05, 10, 1.10) is False


def test_kelly_fraction():
    from kyotei_predictor.betting.bet_sizing import kelly_fraction, BET_SIZING_FIXED, compute_stake
    # f = (b*p - q) / b, b=14, p=0.1, q=0.9 -> (1.4-0.9)/14 = 0.5/14
    f = kelly_fraction(0.1, 15.0)
    assert 0 < f < 0.1
    assert compute_stake(10000, 0.1, 15, BET_SIZING_FIXED, unit_stake=100) == 100
    stake_kelly = compute_stake(10000, 0.1, 15, "kelly_full", unit_stake=100)
    assert 0 <= stake_kelly <= 10000


def test_simulate_bankroll():
    from kyotei_predictor.betting.bankroll_simulation import simulate_bankroll
    bets = [
        {"stake": 100, "odds": 10.0, "hit": True},
        {"stake": 100, "odds": 5.0, "hit": False},
    ]
    r = simulate_bankroll(bets, initial_bankroll=10_000)
    assert r["final_bankroll"] == 10_800  # 10000 - 200 + 1000
    assert r["bet_count"] == 2
    assert r["max_drawdown"] >= 0
    assert "sharpe_ratio" in r
    assert "profit_factor" in r


def test_build_bet_list_from_verify():
    from kyotei_predictor.betting.bankroll_simulation import build_bet_list_from_verify
    predictions = [
        {
            "venue": "A",
            "race_number": 1,
            "selected_bets": ["1-2-3", "2-3-4"],
            "all_combinations": [
                {"combination": "1-2-3", "ratio": 10.0, "probability": 0.1},
                {"combination": "2-3-4", "ratio": 20.0, "probability": 0.05},
            ],
        },
    ]
    details = [
        {"venue": "A", "race_number": 1, "actual": "1-2-3"},
    ]
    bets = build_bet_list_from_verify(predictions, details, fixed_stake=100.0)
    assert len(bets) == 2
    assert bets[0]["stake"] == 100 and bets[0]["odds"] == 10.0 and bets[0]["hit"] is True
    assert bets[1]["hit"] is False
