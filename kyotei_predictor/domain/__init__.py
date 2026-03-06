# domain: 純粋な業務ロジック（I/O なし・CLI なし）
# 検証・予測・ベッティングのデータ構造とメトリクス計算を担当。
# TODO: 段階的に dict ベースの処理を dataclass 化する。

from kyotei_predictor.domain.verification_models import (
    VerificationSummary,
    VerificationDetail,
)
from kyotei_predictor.domain.metrics import (
    compute_roi_pct,
    compute_hit_rate_pct,
    TrialMetrics,
)

__all__ = [
    "VerificationSummary",
    "VerificationDetail",
    "compute_roi_pct",
    "compute_hit_rate_pct",
    "TrialMetrics",
]
