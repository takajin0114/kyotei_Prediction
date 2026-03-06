"""
評価ツールパッケージ

学習済みモデルの評価と分析を行うツール群。
評価指標の分離（hit_rate, mean_reward, ROI 等）は metrics モジュールで行う。
"""

from .evaluate_graduated_reward_model import evaluate_graduated_reward_model

try:
    from .metrics import (
        compute_metrics_from_episodes,
        objective_from_metrics,
        merge_info_into_episode_results,
        OPTIMIZE_FOR_HIT_RATE,
        OPTIMIZE_FOR_MEAN_REWARD,
        OPTIMIZE_FOR_ROI,
        OPTIMIZE_FOR_HYBRID,
    )
    _metrics_exports = (
        'compute_metrics_from_episodes',
        'objective_from_metrics',
        'merge_info_into_episode_results',
        'OPTIMIZE_FOR_HIT_RATE',
        'OPTIMIZE_FOR_MEAN_REWARD',
        'OPTIMIZE_FOR_ROI',
        'OPTIMIZE_FOR_HYBRID',
    )
except ImportError:
    _metrics_exports = ()

__all__ = ['evaluate_graduated_reward_model'] + list(_metrics_exports) 