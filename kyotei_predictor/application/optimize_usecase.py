"""
最適化ユースケース: 段階的報酬モデルのハイパーパラメータ最適化を実行する。

TODO: 現状は tools.optimization.optimize_graduated_reward が実装を保持。段階的に application に寄せる。
"""

from pathlib import Path
from typing import Any, Optional


def run_optimize(
    n_trials: int = 20,
    year_month: Optional[str] = None,
    fast_mode: bool = False,
    medium_mode: bool = False,
    minimal_mode: bool = False,
    data_dir: Optional[Path] = None,
    data_source: str = "db",
    **kwargs: Any,
) -> Any:
    """
    Optuna で最適化を実行し、Study を返す。

    Args:
        n_trials: 試行回数
        year_month: 対象年月 (YYYY-MM)。None で全期間
        fast_mode: 高速モード
        medium_mode: 中速モード
        minimal_mode: 最小限モード（1試行など）
        data_dir: データディレクトリ
        data_source: "file" | "db"
        **kwargs: その他 optimize_graduated_reward に渡すオプション

    Returns:
        Optuna Study オブジェクト
    """
    # TODO: 最適化ロジックを application に移し、domain.metrics を利用する
    from kyotei_predictor.tools.optimization.optimize_graduated_reward import optimize_graduated_reward
    return optimize_graduated_reward(
        n_trials=n_trials,
        year_month=year_month,
        data_dir=str(data_dir) if data_dir else None,
        data_source=data_source,
        fast_mode=fast_mode,
        medium_mode=medium_mode,
        minimal_mode=minimal_mode,
        **kwargs,
    )
