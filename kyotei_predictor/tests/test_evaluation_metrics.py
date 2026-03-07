#!/usr/bin/env python3
"""
評価指標モジュール（metrics）の単体テスト。

- 評価指標が分離して取得できる
- optimize_for の切り替えが効く
"""

import pytest


def test_compute_metrics_from_episodes_basic():
    """指標が分解されて取得できる"""
    from kyotei_predictor.tools.evaluation.metrics import compute_metrics_from_episodes

    rewards = [10.0, -80.0, 50.0, -80.0, 100.0]  # sum=0 → mean_reward=0.0
    hit_count = 2
    payouts = [1000.0, 0.0, 5000.0, 0.0, 10000.0]
    bet_amounts = [100.0] * 5

    m = compute_metrics_from_episodes(rewards, hit_count, payouts, bet_amounts)
    assert m["n_episodes"] == 5
    assert m["hit_rate"] == 0.4
    assert m["mean_reward"] == 0.0
    assert m["hit_count"] == 2
    assert m["total_bet"] == 500.0
    assert m["total_payout"] == 16000.0
    assert m["roi_pct"] == 3200.0  # 16000/500*100


def test_compute_metrics_empty():
    """0エピソードでも安全に動作"""
    from kyotei_predictor.tools.evaluation.metrics import compute_metrics_from_episodes

    m = compute_metrics_from_episodes([], 0, [], [])
    assert m["n_episodes"] == 0
    assert m["hit_rate"] == 0.0
    assert m["mean_reward"] == 0.0
    assert m["roi_pct"] == 0.0


def test_objective_from_metrics_optimize_for():
    """optimize_for の切り替えが効く"""
    from kyotei_predictor.tools.evaluation.metrics import (
        objective_from_metrics,
        OPTIMIZE_FOR_HIT_RATE,
        OPTIMIZE_FOR_MEAN_REWARD,
        OPTIMIZE_FOR_ROI,
        OPTIMIZE_FOR_HYBRID,
    )

    metrics = {"hit_rate": 0.05, "mean_reward": 20.0, "roi_pct": 85.0}

    s_hr = objective_from_metrics(metrics, OPTIMIZE_FOR_HIT_RATE)
    assert s_hr == 5.0  # 0.05 * 100

    s_mr = objective_from_metrics(metrics, OPTIMIZE_FOR_MEAN_REWARD)
    assert s_mr == 20.0

    s_roi = objective_from_metrics(metrics, OPTIMIZE_FOR_ROI)
    assert s_roi == 85.0

    s_hybrid = objective_from_metrics(metrics, OPTIMIZE_FOR_HYBRID)
    assert abs(s_hybrid - (5.0 + 20.0 / 1000.0)) < 1e-6


def test_objective_from_metrics_invalid_falls_back_to_hybrid():
    """不正な optimize_for は hybrid にフォールバック"""
    from kyotei_predictor.tools.evaluation.metrics import objective_from_metrics

    metrics = {"hit_rate": 0.1, "mean_reward": 10.0, "roi_pct": 50.0}
    s = objective_from_metrics(metrics, "invalid_mode")
    assert abs(s - (10.0 + 10.0 / 1000.0)) < 1e-6


def test_merge_info_into_episode_results():
    """info リストから hit_count, payouts, bet_amounts が取り出せる"""
    from kyotei_predictor.tools.evaluation.metrics import merge_info_into_episode_results

    rewards = [1.0, 2.0, 3.0]
    episode_infos = [
        [{"hit": 1, "payout": 100.0, "bet_amount": 100.0}],
        [{"hit": 0, "payout": 0.0, "bet_amount": 100.0}],
        [{"hit": 1, "payout": 200.0, "bet_amount": 100.0}],
    ]
    hit_count, payouts, bet_amounts = merge_info_into_episode_results(rewards, episode_infos)
    assert hit_count == 2
    assert payouts == [100.0, 0.0, 200.0]
    assert bet_amounts == [100.0, 100.0, 100.0]
